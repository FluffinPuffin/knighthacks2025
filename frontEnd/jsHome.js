const elements = document.querySelectorAll('.fade-in');
const header = document.querySelector('.header');
let lastScrollY = window.scrollY;

// Fade-in for people cards (you already had this)
function checkScroll() {
  elements.forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100) {
      el.classList.add('visible');
    }
  });
}

// Fade header on scroll
function handleHeaderScroll() {
    if(window.innerWidth < 500) return; // skip hiding header on tiny phones

    const currentScrollY = window.scrollY;

    if (currentScrollY > lastScrollY && currentScrollY > 100) {
        header.classList.add('hidden');
    } else if (currentScrollY < lastScrollY) {
        header.classList.remove('hidden');
    }

    lastScrollY = currentScrollY;
}


window.addEventListener('scroll', () => {
  checkScroll();
  handleHeaderScroll();
});

checkScroll();
