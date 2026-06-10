# NamLog Demo Recording Checklist

Target length: 10 minutes.

Submission member: Anthony de Klerk (LCS0010203IT). This is a single-member submission because I could not find a group to partake in.

## Before Recording

- Open a terminal in `/Users/tonystark/Documents/DevWork/School/Advanced Programming/Assignment 2`.
- Activate the virtual environment: `source .venv/bin/activate`.
- Run the app: `python main.py` or `python3 main.py`.
- Keep the terminal visible beside the Tkinter window so Flask request logs and `[manifest-worker]` messages can be seen.

## Required Demo Steps

1. Create a delivery in the Tkinter GUI.
   - Use the Deliveries form.
   - Example values: Origin `Walvis Bay`, Destination `Gaborone`, Weight `1200`, Truck ID `1`.
   - Click Submit.
   - Point out the Flask `POST /api/deliveries` log and the new delivery row.

2. View all trucks.
   - Open the Trucks tab.
   - Click Refresh if needed.
   - Point out that the Treeview is populated from `GET /api/trucks`.

3. Prove the background thread is concurrent.
   - Show terminal output containing `[manifest-worker]`.
   - Explain that the GUI and Flask API remain responsive while the worker imports manifest deliveries.

## Code Review Talking Points

- `models.py`: `User` is the abstract base class; `Admin` and `Guest` call `super().__init__()`.
- `DatabaseManager` is a Singleton so the app uses one shared SQLAlchemy engine configuration for SQLite.
- Private attributes such as `__email`, `__capacity_tonnes`, and `__status` are exposed through `@property` getters and validated setters.

## Final Upload Check

- Confirm `README.md` identifies Anthony de Klerk (LCS0010203IT) as the single member.
- Create the public GitHub repository named `advanced-programing_LCS0010203it_AnthonydeKlerk` and push the assignment files.
- Upload `NamLog_Assignment_3_Presentation.pptx`.
- Upload the compressed MP4/MPEG screen recording.
- Submit the shared folder link and public GitHub repository link as required.
