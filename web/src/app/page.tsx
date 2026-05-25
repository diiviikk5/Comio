"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [scrolled, setScrolled] = useState(false);

  /* ─── Scroll listener for navbar ────────────────────────── */
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      {/* ══════════════ NAVBAR ══════════════ */}
      <nav className={`navbar${scrolled ? " scrolled" : ""}`}>
        <div className="container navbar-inner">
          <div className="navbar-logo">COMIO</div>
          <div className="navbar-links">
            <a
              href="https://github.com/diiviikk5/Comio"
              target="_blank"
              rel="noopener noreferrer"
              className="navbar-cta"
            >
              Star on GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* ══════════════ HERO SPLIT SECTION ══════════════ */}
      <section className="hero-split" id="hero">
        <div className="hero-bg" />
        <div className="container hero-split-inner">
          
          {/* Left Column: Text & Features List & Download Actions */}
          <div className="hero-split-left">
            <h1 className="hero-title">COMIO</h1>
            <p className="hero-subtitle">A high-performance desktop comic reader</p>
            <p className="hero-description">
              An open-source, distraction-free desktop application for organizing and reading 
              CBR, CBZ, and PDF comic archives. Beautifully engineered, fully multi-threaded, 
              and directly integrated with the Internet Archive library.
            </p>

            {/* Checklist with premium numbered indexes */}
            <div className="hero-checklist">
              <div className="checklist-item">
                <span className="checklist-icon">01</span>
                <div className="checklist-content">
                  <h3 className="checklist-title">Local Library Import</h3>
                  <p className="checklist-desc">Seamlessly import local CBR, CBZ, ZIP, and RAR archives with on-demand background page extraction.</p>
                </div>
              </div>

              <div className="checklist-item">
                <span className="checklist-icon">02</span>
                <div className="checklist-content">
                  <h3 className="checklist-title">Internet Archive Integration</h3>
                  <p className="checklist-desc">Directly query and download from a catalog of over 10,000 public domain comic books inside the reader.</p>
                </div>
              </div>

              <div className="checklist-item">
                <span className="checklist-icon">03</span>
                <div className="checklist-content">
                  <h3 className="checklist-title">Advanced Viewing Engine</h3>
                  <p className="checklist-desc">Read comfortably with custom color filters (sepia, warm, dim), double-page spread views, and smooth canvas panning.</p>
                </div>
              </div>
            </div>

            {/* Download CTA Controls */}
            <div className="hero-split-actions">
              <div className="action-row">
                <a href="#" className="btn btn-primary btn-lg btn-glow">
                  Download for Free
                </a>
              </div>
              <div className="action-row">
                <span className="platform-badge">Windows</span>
                <span className="platform-badge">macOS</span>
                <span className="platform-badge">Linux</span>
              </div>
              <span className="hero-split-meta">
                v1.0.0 · ~45 MB · Requires 64-bit OS
              </span>
            </div>
          </div>

          {/* Right Column: Styled App Demo Video */}
          <div className="hero-split-right">
            <div className="video-frame-wrapper animate-on-scroll is-visible">
              <video 
                className="video-frame" 
                src="/comio-landing.mp4" 
                autoPlay 
                loop 
                muted 
                playsInline
                controls={false}
              />
            </div>
          </div>

        </div>
      </section>

      {/* ══════════════ FOOTER ══════════════ */}
      <footer className="footer">
        <div className="container footer-inner">
          <p className="footer-powered">
            Powered by Internet Archive
          </p>
          <div className="footer-links">
            <a href="https://github.com/diiviikk5/Comio" target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href="#">Privacy</a>
            <a href="#">License</a>
          </div>
          <p className="footer-copyright">
            © {new Date().getFullYear()} COMIO. All rights reserved.
          </p>
        </div>
      </footer>
    </>
  );
}
