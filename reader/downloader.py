"""
COMIO — Download Manager
Threaded download queue with progress tracking and auto-import.
"""

import os
import time
import urllib.request
import urllib.error
from typing import Optional
from dataclasses import dataclass
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker


@dataclass
class DownloadTask:
    """Represents a single download."""
    url: str
    filename: str
    destination: str  # Output directory
    identifier: str = ""  # IA identifier
    title: str = ""
    total_size: int = 0
    downloaded: int = 0
    speed: float = 0  # bytes/sec
    status: str = "queued"  # queued, downloading, completed, failed, cancelled
    error: str = ""

    @property
    def output_path(self) -> str:
        return os.path.join(self.destination, self.filename)

    @property
    def progress(self) -> float:
        if self.total_size <= 0:
            return 0
        return min(100, (self.downloaded / self.total_size) * 100)

    @property
    def eta_seconds(self) -> float:
        if self.speed <= 0:
            return 0
        remaining = self.total_size - self.downloaded
        return remaining / self.speed

    @property
    def speed_display(self) -> str:
        if self.speed < 1024:
            return f"{self.speed:.0f} B/s"
        elif self.speed < 1024 * 1024:
            return f"{self.speed / 1024:.1f} KB/s"
        else:
            return f"{self.speed / (1024 * 1024):.1f} MB/s"

    @property
    def size_display(self) -> str:
        if self.total_size < 1024:
            return f"{self.total_size} B"
        elif self.total_size < 1024 * 1024:
            return f"{self.total_size / 1024:.1f} KB"
        else:
            return f"{self.total_size / (1024 * 1024):.1f} MB"


class DownloadWorker(QThread):
    """Worker thread that downloads a single file."""
    progress_updated = pyqtSignal(str, int, int, float)  # url, downloaded, total, speed
    download_completed = pyqtSignal(str, str)  # url, output_path
    download_failed = pyqtSignal(str, str)  # url, error
    
    CHUNK_SIZE = 8192  # 8KB chunks
    
    def __init__(self, task: DownloadTask, parent=None):
        super().__init__(parent)
        self._task = task
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        task = self._task
        try:
            # Create destination directory
            os.makedirs(task.destination, exist_ok=True)
            
            # Open connection
            req = urllib.request.Request(task.url)
            req.add_header("User-Agent", "COMIO Comic Reader/1.0")
            
            # Support resume
            if os.path.exists(task.output_path):
                existing_size = os.path.getsize(task.output_path)
                req.add_header("Range", f"bytes={existing_size}-")
                mode = "ab"
            else:
                existing_size = 0
                mode = "wb"
            
            response = urllib.request.urlopen(req, timeout=30)
            
            # If server ignored Range and returned 200 OK, reset to overwrite mode
            if response.getcode() == 200:
                existing_size = 0
                mode = "wb"
            
            # Get total size
            content_length = response.headers.get("Content-Length")
            if content_length:
                task.total_size = int(content_length) + existing_size
            
            # Download with progress
            task.downloaded = existing_size
            start_time = time.time()
            last_report_time = start_time
            bytes_since_report = 0
            
            with open(task.output_path, mode) as f:
                while not self._cancelled:
                    chunk = response.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    task.downloaded += len(chunk)
                    bytes_since_report += len(chunk)
                    
                    # Calculate speed every 0.5 seconds
                    now = time.time()
                    elapsed = now - last_report_time
                    if elapsed >= 0.5:
                        task.speed = bytes_since_report / elapsed
                        bytes_since_report = 0
                        last_report_time = now
                        self.progress_updated.emit(
                            task.url, task.downloaded, task.total_size, task.speed
                        )
            
            if self._cancelled:
                task.status = "cancelled"
                return
            
            task.status = "completed"
            self.download_completed.emit(task.url, task.output_path)
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.download_failed.emit(task.url, str(e))
class DownloadManager(QObject):
    """
    Manages a queue of downloads with concurrent download support.
    Emits thread-safe Qt signals for GUI updates.
    """
    progress_updated = pyqtSignal(object)   # DownloadTask
    download_completed = pyqtSignal(object) # DownloadTask
    download_failed = pyqtSignal(object)    # DownloadTask
    
    def __init__(self, max_concurrent: int = 2):
        super().__init__()
        self._queue: list[DownloadTask] = []
        self._active: dict[str, DownloadWorker] = {}  # url -> worker
        self._completed: list[DownloadTask] = []
        self._max_concurrent = max_concurrent
        self._mutex = QMutex()
    
    def add_download(self, url: str, filename: str, destination: str,
                      identifier: str = "", title: str = "") -> DownloadTask:
        """Add a download to the queue."""
        task = DownloadTask(
            url=url,
            filename=filename,
            destination=destination,
            identifier=identifier,
            title=title or filename,
        )
        
        with QMutexLocker(self._mutex):
            self._queue.append(task)
        
        self._process_queue()
        return task
    
    def _process_queue(self):
        """Start downloads if slots are available."""
        with QMutexLocker(self._mutex):
            while self._queue and len(self._active) < self._max_concurrent:
                task = self._queue.pop(0)
                task.status = "downloading"
                
                worker = DownloadWorker(task)
                worker.progress_updated.connect(self._on_progress)
                worker.download_completed.connect(self._on_completed)
                worker.download_failed.connect(self._on_failed)
                
                self._active[task.url] = worker
                worker.start()
    
    def _on_progress(self, url: str, downloaded: int, total: int, speed: float):
        """Handle download progress update."""
        task = self._find_active_task(url)
        if task:
            self.progress_updated.emit(task)
    
    def _on_completed(self, url: str, output_path: str):
        """Handle download completion."""
        with QMutexLocker(self._mutex):
            worker = self._active.pop(url, None)
            if worker:
                task = worker._task
                self._completed.append(task)
                self.download_completed.emit(task)
        
        self._process_queue()
    
    def _on_failed(self, url: str, error: str):
        """Handle download failure."""
        with QMutexLocker(self._mutex):
            worker = self._active.pop(url, None)
            if worker:
                task = worker._task
                self.download_failed.emit(task)
        
        self._process_queue()
    
    def _find_active_task(self, url: str) -> Optional[DownloadTask]:
        """Find a task by URL in active downloads."""
        worker = self._active.get(url)
        return worker._task if worker else None
    
    def cancel_download(self, url: str):
        """Cancel a specific download."""
        with QMutexLocker(self._mutex):
            # Check active
            worker = self._active.pop(url, None)
            if worker:
                worker.cancel()
                return
            
            # Check queue
            self._queue = [t for t in self._queue if t.url != url]
    
    def cancel_all(self):
        """Cancel all downloads."""
        with QMutexLocker(self._mutex):
            for worker in self._active.values():
                worker.cancel()
            self._active.clear()
            self._queue.clear()
    
    @property
    def active_count(self) -> int:
        return len(self._active)
    
    @property
    def queue_count(self) -> int:
        return len(self._queue)
    
    @property
    def all_tasks(self) -> list[DownloadTask]:
        tasks = list(self._queue)
        tasks.extend(w._task for w in self._active.values())
        tasks.extend(self._completed)
        return tasks
