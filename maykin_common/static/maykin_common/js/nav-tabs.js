// See https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/tab_role
// for the accessibility requirements.

const initTabs = () => {
    const tabNodes = document.querySelectorAll('.tabs');
    for (const node of tabNodes) {
        const tabList = node.querySelector('[role="tablist"]');
        const tabs = tabList.querySelectorAll(':scope > [role="tab"]');

        // Handle clicks on each tab to activate the associated panel
        for (const tabBtn of tabs) {
            tabBtn.addEventListener('click', () => {
                // ignore if it's already active
                if (tabBtn.getAttribute('aria-selected') === 'true') {
                    return;
                }

                // Remove all current selected tabs
                // and remove the active class from the active button and pane
                tabList
                    .querySelectorAll(':scope > [aria-selected="true"]')
                    .forEach(tab => {
                        tab.setAttribute("aria-selected", false);
                        tab.classList.remove('tabs__item--active');
                        const panelId = tab.getAttribute('aria-controls');
                        const panel = node.querySelector(`#${panelId}`);
                        panel.setAttribute('hidden', true)
                    });

                // mark this tab as selected/active
                tabBtn.setAttribute('aria-selected', true);
                tabBtn.classList.add('tabs__item--active');

                // lookup the panel to activate
                const panelId = tabBtn.getAttribute('aria-controls');
                const panel = node.querySelector(`#${panelId}`);
                panel.removeAttribute('hidden');
            });
        }

        let tabFocusIndex = 0;

        // Handle keyboard navigation to focus other tabs
        tabList.addEventListener('keydown', event => {
            // move right or left -> remove tab focus from current tab
            if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
              tabs[tabFocusIndex].setAttribute("tabindex", -1);

              if (event.key === "ArrowRight") {
                tabFocusIndex++;
                // If we're at the end, go to the start
                if (tabFocusIndex >= tabs.length) {
                  tabFocusIndex = 0;
                }
                // Move left
              } else if (event.key === "ArrowLeft") {
                tabFocusIndex--;
                // If we're at the start, move to the end
                if (tabFocusIndex < 0) {
                  tabFocusIndex = tabs.length - 1;
                }
              }

              tabs[tabFocusIndex].setAttribute("tabindex", 0);
              tabs[tabFocusIndex].focus();
            }
        });
    }
};

initTabs();
