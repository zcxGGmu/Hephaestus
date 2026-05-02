const revealItems = document.querySelectorAll("[data-reveal]");
const langButtons = document.querySelectorAll("[data-set-lang]");
const body = document.body;

const setLanguage = (lang) => {
  body.dataset.lang = lang;
  localStorage.setItem("hephaestus-site-lang", lang);
  langButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.setLang === lang);
  });
};

const storedLanguage = localStorage.getItem("hephaestus-site-lang");
if (storedLanguage === "zh" || storedLanguage === "en") {
  setLanguage(storedLanguage);
}

langButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setLanguage(button.dataset.setLang || "en");
  });
});

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      }
    },
    { threshold: 0.14 }
  );

  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}
