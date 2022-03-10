const socket = io()

function setupMainMenu() {
    let mainMenu = document.getElementById('main_menu')
    if (!mainMenu)
        return

    let mainMenuItems = mainMenu.children

    if (mainMenuItems.length === 1) {
        let mainMenuItem = mainMenuItems[0]

        document.addEventListener('keyup', (ev) => {
            if (ev.key === 'Escape') {
                window.location.href = mainMenuItem.dataset.url
            }
        })

        return
    }

    for (let i = 0, j = 1; i < mainMenuItems.length; ++i, ++j) {
        let mainMenuItem = mainMenuItems[i]

        document.addEventListener('keyup', (ev) => {
            if (ev.key === j.toString()) {
                window.location.href = mainMenuItem.dataset.url
            }
        })
    }
}

window.addEventListener('load', () => {
    setupMainMenu()
})
