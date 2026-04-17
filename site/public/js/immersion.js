/**
 * Kiosko Azul - Immersion System 2.0
 * Handles preloader, ambient layers, and interactive water effects.
 */

class ImmersionSystem {
  constructor() {
    this.init();
  }

  init() {
    this.createBackgroundLayers();
    this.createParticles();
    this.setupInteractivity();
    this.handleBackgroundVideos();
    this.handlePreloader();
  }

  createBackgroundLayers() {
    // Inject grain and caustics if missing
    if (!document.querySelector('.grain-texture')) {
      const grain = document.createElement('div');
      grain.className = 'grain-texture';
      document.body.prepend(grain);
    }
    if (!document.querySelector('.water-caustics')) {
      const caustics = document.createElement('div');
      caustics.className = 'water-caustics';
      document.body.prepend(caustics);
    }
    // Container for foam
    if (!document.getElementById('sea-foam-container')) {
      const foam = document.createElement('div');
      foam.id = 'sea-foam-container';
      document.body.prepend(foam);
    }
  }

  handlePreloader() {
    const preloader = document.getElementById('preloader');
    if (!preloader) return;

    // Generate preloader bubbles
    const bubbleContainer = preloader.querySelector('.preloader-bubbles');
    if (bubbleContainer) {
      for (let i = 0; i < 20; i++) {
        const b = document.createElement('div');
        b.className = 'p-bubble';
        const size = Math.random() * 15 + 5 + 'px';
        b.style.width = size;
        b.style.height = size;
        b.style.left = Math.random() * 100 + '%';
        b.style.animationDelay = Math.random() * 4 + 's';
        b.style.animationDuration = Math.random() * 3 + 2 + 's';
        bubbleContainer.appendChild(b);
      }
    }

    const dismiss = () => {
      if (this.preloaderDismissed) return;
      this.preloaderDismissed = true;
      
      setTimeout(() => {
        preloader.classList.add('fade-out');
        document.body.classList.add('surfaced');
        // Clean up DOM after fade
        setTimeout(() => {
          if (preloader.parentNode) preloader.style.display = 'none';
        }, 1500);
      }, 500);
    };

    if (document.readyState === 'complete') {
      dismiss();
    } else {
      window.addEventListener('load', dismiss);
      // Fallback: don't stay stuck more than 5 seconds
      setTimeout(dismiss, 5000);
    }
  }

  handleBackgroundVideos() {
    const videoDia = document.getElementById('video-dia');
    const videoNoche = document.getElementById('video-noche');
    const videoTarde = document.getElementById('video-tarde');
    
    if (!videoDia && !videoNoche && !videoTarde) return;

    const currentHour = new Date().getHours();
    let activeVideo = null;

    // Logic: 6AM-4PM (Day), 4PM-7PM (Afternoon), 7PM-6AM (Night)
    if (currentHour >= 6 && currentHour < 16) {
      activeVideo = videoDia;
    } else if (currentHour >= 16 && currentHour < 19) {
      activeVideo = videoTarde;
    } else {
      activeVideo = videoNoche;
    }

    [videoDia, videoNoche, videoTarde].forEach(v => {
      if (!v) return;
      if (v === activeVideo) {
        v.classList.add('active');
        v.play().catch(() => console.log("Auto-play prevented"));
      } else {
        v.classList.remove('active');
        // Wait for fade out then pause
        setTimeout(() => {
          if (!v.classList.contains('active')) v.pause();
        }, 1500);
      }
    });
  }

  createParticles() {
    const container = document.getElementById('sea-foam-container');
    if (!container) return;

    this.particles = [];
    for (let i = 0; i < 25; i++) {
      const p = document.createElement('div');
      p.className = 'sea-foam-particle';
      const size = Math.random() * 30 + 10;
      p.style.width = size + 'px';
      p.style.height = size + 'px';
      
      const particle = {
        el: p,
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        targetX: 0,
        targetY: 0
      };
      
      container.appendChild(p);
      this.particles.push(particle);
    }

    this.animateParticles();
  }

  animateParticles() {
    this.particles.forEach(p => {
      // Natural floating movement with slight wobble
      p.x += p.vx + Math.sin(Date.now() * 0.001 + p.x) * 0.1;
      p.y += p.vy + Math.cos(Date.now() * 0.001 + p.y) * 0.1;

      // Wrap around
      if (p.x < -100) p.x = window.innerWidth + 100;
      if (p.x > window.innerWidth + 100) p.x = -100;
      if (p.y < -100) p.y = window.innerHeight + 100;
      if (p.y > window.innerHeight + 100) p.y = -100;

      // Apply smooth mouse interaction influence
      const dx = this.mouseX - p.x;
      const dy = this.mouseY - p.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 250) {
        // Gently push away from mouse rather than snap
        const force = (250 - dist) * 0.005;
        p.vx -= dx * force * 0.01;
        p.vy -= dy * force * 0.01;
        
        // Cap velocity for harmony
        p.vx = Math.max(-1, Math.min(1, p.vx));
        p.vy = Math.max(-1, Math.min(1, p.vy));
        
        p.el.style.opacity = '0.3';
      } else {
        // Friction to return to calm state
        p.vx *= 0.99;
        p.vy *= 0.99;
        p.el.style.opacity = '0.15';
      }

      p.el.style.transform = `translate(${p.x}px, ${p.y}px)`;
    });

    requestAnimationFrame(() => this.animateParticles());
  }

  setupInteractivity() {
    this.mouseX = -1000;
    this.mouseY = -1000;

    window.addEventListener('mousemove', (e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
      this.updateCaustics(e);
    });

    window.addEventListener('touchstart', (e) => {
      this.mouseX = e.touches[0].clientX;
      this.mouseY = e.touches[0].clientY;
    });
  }

  updateCaustics(e) {
    const caustics = document.querySelector('.water-caustics');
    if (!caustics) return;
    
    const moveX = (e.clientX - window.innerWidth / 2) * 0.015;
    const moveY = (e.clientY - window.innerHeight / 2) * 0.015;
    
    caustics.style.transform = `translate(${moveX}px, ${moveY}px)`;
  }
}

// Initialize on execution
window.immersion = new ImmersionSystem();
