"use client";

import { useEffect, useState, useRef } from "react";

/* ─── Comic cover placeholder data ──────────────────────── */
const COMICS = [
  { title: "The Phantom Realm", gradient: "linear-gradient(135deg, #1a1a2e, #16213e, #0f3460)" },
  { title: "Crimson Thunder", gradient: "linear-gradient(135deg, #2d1b1b, #4a1515, #6b2020)" },
  { title: "Stellar Odyssey", gradient: "linear-gradient(135deg, #0d1b2a, #1b2838, #1e3a5f)" },
  { title: "Emerald Knight", gradient: "linear-gradient(135deg, #1a2e1a, #1e3e1e, #205020)" },
  { title: "Dark Archives", gradient: "linear-gradient(135deg, #1a1a1a, #2a2020, #3a2525)" },
  { title: "Neon Samurai", gradient: "linear-gradient(135deg, #1a1a2e, #2e1a3e, #4a1a4a)" },
];

const FEATURES = [
  {
    icon: "⚡",
    title: "Lightning Fast",
    desc: "Buttery smooth page rendering with hardware-accelerated zoom, pan, and scroll.",
  },
  {
    icon: "📚",
    title: "Internet Archive",
    desc: "Search and download 10,000+ free public domain comics directly in the app.",
  },
  {
    icon: "📦",
    title: "All Formats",
    desc: "CBR, CBZ, ZIP, RAR — every comic format handled with on-demand page extraction.",
  },
  {
    icon: "📖",
    title: "Reading Modes",
    desc: "Single page, double-page spread, vertical scroll, manga RTL support.",
  },
];

export default function Home() {
  const [scrolled, setScrolled] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);

  /* ─── Scroll listener for navbar ────────────────────────── */
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  /* ─── IntersectionObserver for scroll animations ────────── */
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    );

    const elements = document.querySelectorAll(".animate-on-scroll");
    elements.forEach((el) => observerRef.current?.observe(el));

    return () => observerRef.current?.disconnect();
  }, []);

  /* ─── Smooth scroll handler ─────────────────────────────── */
  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      {/* ══════════════ NAVBAR ══════════════ */}
      <nav className={`navbar${scrolled ? " scrolled" : ""}`}>
        <div className="container navbar-inner">
          <div className="navbar-logo">COMIO</div>
          <div className="navbar-links">
            <a href="#features" onClick={(e) => { e.preventDefault(); scrollTo("features"); }}>
              <span className="nav-link-text">Features</span>
            </a>
            <a href="#comics" onClick={(e) => { e.preventDefault(); scrollTo("comics"); }}>
              <span className="nav-link-text">Browse</span>
            </a>
            <a
              href="#download"
              className="navbar-cta"
              onClick={(e) => { e.preventDefault(); scrollTo("download"); }}
            >
              Download
            </a>
          </div>
        </div>
      </nav>

      {/* ══════════════ HERO ══════════════ */}
      <section className="hero" id="hero">
        <div className="hero-bg" />
        <div className="hero-content">
          <h1 className="hero-title">COMIO</h1>
          <p className="hero-subtitle">The comic reader that sets your collection free</p>
          <p className="hero-description">
            Explore thousands of free comics from the Internet Archive. A beautiful, 
            blazing-fast reader for every format — no subscriptions, no ads, just comics.
          </p>
          <div className="hero-actions">
            <a
              href="#download"
              className="btn btn-primary btn-lg"
              onClick={(e) => { e.preventDefault(); scrollTo("download"); }}
            >
              Download Free
            </a>
            <a
              href="#comics"
              className="btn btn-outline btn-lg"
              onClick={(e) => { e.preventDefault(); scrollTo("comics"); }}
            >
              Browse Comics
            </a>
          </div>
        </div>

        <div className="hero-stats">
          <span>10,000+ Free Comics</span>
          <span className="hero-stats-divider" />
          <span>CBR / CBZ Support</span>
          <span className="hero-stats-divider" />
          <span>Internet Archive Powered</span>
        </div>
      </section>

      {/* ══════════════ FEATURES ══════════════ */}
      <section className="section section-dark" id="features">
        <div className="container">
          <div className="animate-on-scroll">
            <h2 className="section-title">Why COMIO?</h2>
            <span className="section-accent" />
          </div>
          <div className="features-grid stagger-children">
            {FEATURES.map((f, i) => (
              <div
                key={i}
                className="feature-card animate-on-scroll"
                style={{ transitionDelay: `${i * 0.1}s` }}
              >
                <span className="feature-icon">{f.icon}</span>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════ COMIC SHOWCASE ══════════════ */}
      <section className="section" id="comics">
        <div className="container">
          <div className="animate-on-scroll">
            <h2 className="section-title">Discover Free Comics</h2>
            <span className="section-accent" />
            <p className="section-subtitle">
              Browse and read thousands of public domain comics from the Internet Archive, 
              right inside COMIO.
            </p>
          </div>
          <div className="comics-grid stagger-children">
            {COMICS.map((c, i) => (
              <div
                key={i}
                className="comic-card animate-on-scroll"
                style={{ transitionDelay: `${i * 0.08}s` }}
              >
                <div
                  className="comic-cover"
                  style={{ background: c.gradient }}
                >
                  <div className="comic-title-overlay">{c.title}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════ DOWNLOAD ══════════════ */}
      <section className="section download-section" id="download">
        <div className="container">
          <div className="animate-on-scroll">
            <h2 className="download-title">Get COMIO</h2>
            <p className="download-subtitle">Free, open source, no ads</p>
          </div>

          <div className="download-btn animate-on-scroll">
            <a href="#" className="btn btn-primary btn-lg btn-glow">
              ⬇ Download for Free
            </a>
          </div>

          <div className="platforms animate-on-scroll">
            <span className="platform-badge">🪟 Windows</span>
            <span className="platform-badge">🍎 macOS</span>
            <span className="platform-badge">🐧 Linux</span>
          </div>

          <p className="download-meta animate-on-scroll">
            v1.0.0 · ~45 MB · Requires 64-bit OS
          </p>

          <a
            href="https://github.com"
            className="download-github animate-on-scroll"
            target="_blank"
            rel="noopener noreferrer"
          >
            ★ Star on GitHub
          </a>
        </div>
      </section>

      {/* ══════════════ FOOTER ══════════════ */}
      <footer className="footer">
        <div className="container footer-inner">
          <p className="footer-powered">
            Powered by Internet Archive ❤️
          </p>
          <div className="footer-links">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
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
