export function createRovingTabs(tabs, panels, { initialIndex = 0 } = {}) {
  // TODO: synchronize ARIA/panels and install click/keyboard behavior.
  return { activeIndex: -1, select() { return false; }, destroy() {} };
}
