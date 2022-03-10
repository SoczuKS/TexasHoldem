window.addEventListener('load', () => {
    let humanPlayerNumberSelector = document.getElementById('number_of_human_players')
    let cpuPlayerNumberSelector = document.getElementById('number_of_cpu_players')

    humanPlayerNumberSelector.addEventListener('change', (ev) => {
        checkMinMax(ev.target)

        if (parseInt(ev.target.value) > 1) {
            cpuPlayerNumberSelector.min = 0
        } else {
            cpuPlayerNumberSelector. min = 1
        }

        setupHumanPlayersDiv()

        cpuPlayerNumberSelector.max = 8 - parseInt(ev.target.value)

        checkMinMax(cpuPlayerNumberSelector)
    })

    cpuPlayerNumberSelector.addEventListener('change', (ev) => {
        checkMinMax(ev.target)

        if (parseInt(ev.target.value) >= 1) {
            humanPlayerNumberSelector.min = 1
        } else {
            humanPlayerNumberSelector.min = 2
        }

        setupCpuPlayersDiv()

        humanPlayerNumberSelector.max = 8 - parseInt(ev.target.value)

        checkMinMax(humanPlayerNumberSelector)
    })
})

function checkMinMax(element) {
    if (parseInt(element.value) > parseInt(element.max)) {
        element.value = element.max
        element.dispatchEvent(new Event('change'))
    } else if (parseInt(element.value) < parseInt(element.min)) {
        element.value = element.min
        element.dispatchEvent(new Event('change'))
    }
}

function setupHumanPlayersDiv() {
    let humanPlayerNamesDiv = document.getElementById('human_players')
    let humanPlayerNumberSelector = document.getElementById('number_of_human_players')
    let requiredNumberOfPlayers = parseInt(humanPlayerNumberSelector.value)

    if (humanPlayerNamesDiv.children.length > requiredNumberOfPlayers) {
        do {
            humanPlayerNamesDiv.removeChild(humanPlayerNamesDiv.lastChild)
        } while (humanPlayerNamesDiv.children.length !== requiredNumberOfPlayers)
    } else if (humanPlayerNamesDiv.children.length < requiredNumberOfPlayers) {
        do {
            let formRow = document.createElement('label')
            formRow.innerText = "Nazwa gracza " + (humanPlayerNamesDiv.children.length + 1).toString()

            let input = document.createElement('input')
            input.value = 'Gracz ' + (humanPlayerNamesDiv.children.length + 1).toString()
            input.type = 'text'
            input.name = 'players[]'
            input.required = true

            formRow.appendChild(input)
            humanPlayerNamesDiv.appendChild(formRow)
        } while (humanPlayerNamesDiv.children.length !== requiredNumberOfPlayers)
    }
}

function setupCpuPlayersDiv() {
    let cpuPlayerTypesDiv = document.getElementById('cpu_players')
    let cpuPlayerNumberSelector = document.getElementById('number_of_cpu_players')
    let requiredNumberOfPlayers = parseInt(cpuPlayerNumberSelector.value)

    console.log(requiredNumberOfPlayers)

    if (cpuPlayerTypesDiv.children.length > requiredNumberOfPlayers) {
        do {
            cpuPlayerTypesDiv.removeChild(cpuPlayerTypesDiv.lastChild)
        } while (cpuPlayerTypesDiv.children.length !== requiredNumberOfPlayers)
    } else {
        let cpuTypes = [
            'Ostrożny',
            'Normalny',
            'Agresywny',
            'Losowo'
        ]

        do {
            let formRow = document.createElement('label')
            formRow.innerText = "Typ CPU " + (cpuPlayerTypesDiv.children.length + 1)

            let select = document.createElement('select')
            select.name = 'cpu_types[]'

            for (let i = 0; i < cpuTypes.length; ++i) {
                let option = document.createElement('option')
                option.value = i.toString()
                option.text = cpuTypes[i]
                select.appendChild(option)
            }

            select.value = '1'
            formRow.appendChild(select)
            cpuPlayerTypesDiv.appendChild(formRow)
            console.log('Dodaję')
        } while (cpuPlayerTypesDiv.children.length !== requiredNumberOfPlayers)
    }
}
