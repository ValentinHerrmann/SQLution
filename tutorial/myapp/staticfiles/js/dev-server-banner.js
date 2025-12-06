(function () {
      try {
        let host = String(globalThis.location?.hostname || '').toLowerCase();
        let isDev = host.includes('dev') || host.includes('tmp');
        if (!isDev) return;
        let banner = document.createElement('div');
        banner.textContent = 'Dev Server';
        banner.style.position = 'fixed';
        banner.style.top = '40px';
        banner.style.left = '-90px';
        banner.style.padding = '8px 100px';
        banner.style.background = 'rgba(255, 0, 0, 0.50)'; // make this 35% opacity red
        banner.style.color = '#fff';
        banner.style.fontWeight = '700';
        banner.style.fontSize = '14px';
        banner.style.letterSpacing = '2px';
        banner.style.transform = 'rotate(-45deg)';
        banner.style.transformOrigin = 'center';
        banner.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
        banner.style.zIndex = '11000';
        banner.style.pointerEvents = 'none';
        banner.style.userSelect = 'none';
        document.body.appendChild(banner);
      } catch (e) {
        console.warn('Dev banner error', e);
      }
    })();