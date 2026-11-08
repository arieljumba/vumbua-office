(() => {
  const toggle = document.querySelector("[data-menu-toggle]");
  const nav = document.querySelector("[data-nav]");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const isOpen = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!isOpen));
      nav.classList.toggle("is-open", !isOpen);
    });

    nav.addEventListener("click", (event) => {
      if (event.target instanceof HTMLAnchorElement) {
        toggle.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
      }
    });
  }

  const revealItems = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealItems.length) {
    const observer = new IntersectionObserver(
      (entries, currentObserver) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            currentObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 },
    );
    revealItems.forEach((element) => observer.observe(element));
  } else {
    revealItems.forEach((element) => element.classList.add("is-visible"));
  }
})();
