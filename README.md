# Super-ultra-project

Super-ultra-project is a small Pygame-based game created as an OOP study project by students of Shevchenko National University of Kyiv. The project demonstrates a simple menu system, button widgets, and a settings screen (audio/fullscreen toggles) implemented with classes.

## Features

- Main menu with START, EXIT and SETTINGS buttons.
- Settings menu with AUDIO toggle, fullscreen toggle, and BACK
- Reusable `Button` class and menu system (`Menu`, `MainMenu`, `SettingsMenu`)

## Requirements

- Python 3.10+ (typed hints use modern syntax)
- pygame

Install Python packages using the provided `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

## Run

From the project root run:

```powershell
python main.py
```

The game opens a window with a background image and the main menu. Use the mouse to hover and click buttons.

## Controls

- Mouse hover highlights buttons
- Left click to activate a button
- START currently prints "START" to console (placeholder for gameplay)
- EXIT closes the game
- SETTINGS opens the settings menu where you can toggle audio and fullscreen

## Project structure

```
.
├─ main.py            # Main application and classes (Button, Menu, App)
├─ requirements.txt   # Python dependencies (pygame)
├─ README.md
├─ fonts/
│   └─ menu_font.ttf
└─ images/
	├─ bg_menu.jpg
	└─ smug.png
```

## Notes & Troubleshooting

- If you see errors about missing fonts or images, ensure the `fonts` and `images` folders are present and contain the files listed above.
- If the app fails to start with an import or syntax error, confirm you're using Python 3.10+ and that `pygame` is installed.
- Fullscreen toggle uses `pygame.display.set_mode(...)` — if your display behaves oddly after toggling, close and reopen the app.
- Buttons' `on_click` handlers expect callable functions. If you add buttons, ensure `on_click` is not `None` or add checks before calling.

## Contributing

This is an educational project — contributions are welcome. Keep changes focused and small. If you add features (actual gameplay, audio handling, persistent settings), consider:

- Adding unit tests where practical
- Updating the README with new usage notes
- Keeping assets in `images/` or `fonts/` folders

## License

This repository does not include a license file.
