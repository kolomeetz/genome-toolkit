import '@testing-library/jest-dom'

// JSDOM does not implement scrollTo; stub it globally
window.HTMLElement.prototype.scrollTo = () => {}
