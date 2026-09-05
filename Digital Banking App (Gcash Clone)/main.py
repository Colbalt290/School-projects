import PySimpleGUI as sg

#Define the window's contents
layout = [[sg.Text("Welcome to Aurion's Digital Banking Service.")],
          [sg.Text("Username:")],
          [sg.Input(key='-INPUT-')],
          [sg.Text("Password:")],
          [sg.Input(key='-INPUT-')],
          [sg.Text(size=(40,1), key='-OUTPUT-')],
          [sg.Button('Login')],[sg.Button('Quit')]]

#Create the window
window = sg.Window('Aurion Banking Service', layout)

#Display and interact with the Window using an Event Loop
while True:
    event, values = window.read()
    #Check if user is wants to quit or window was closed
    if event == sg.WINDOW_CLOSED or event == 'Quit':
        break
    # Output a message to the window
    window['-OUTPUT-'].update('Hello ' + values['-INPUT-'] + "! Thanks for trying PySimpleGUI")

# Finish up by removing from the screen
window.close()