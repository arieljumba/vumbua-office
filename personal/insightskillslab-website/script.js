const revealItems = document.querySelectorAll('.reveal');

const revealObserver = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        revealObserver.unobserve(entry.target);
      }
    }
  },
  {
    threshold: 0.15,
  }
);

for (const item of revealItems) {
  revealObserver.observe(item);
}

const year = document.getElementById('year');
if (year) {
  year.textContent = new Date().getFullYear();
}

const currentPath = window.location.pathname.split('/').pop() || 'index.html';
const navLinks = document.querySelectorAll('[data-nav]');
for (const link of navLinks) {
  const href = link.getAttribute('href');
  if (href === currentPath) {
    link.classList.add('is-active');
  }
}
