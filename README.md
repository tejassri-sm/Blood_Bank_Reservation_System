# Blood-Bank-Reservation-System

<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=220&text=BLOOD%20BANK%20RESERVATION%20SYSTEM&fontSize=32&fontColor=FFFFFF&fontAlignY=38&desc=CONNECT%20DONORS%20%2F%2F%20SAVE%20LIVES&descAlignY=60&descSize=15&animation=fadeIn&color=0:09090B,45:7F1D1D,100:EF4444" alt="Blood Bank Reservation System banner"/>

<br/>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=17&duration=2800&pause=800&color=FF4D6D&center=true&vCenter=true&width=650&lines=Every+Drop+Counts.;Smart+Blood+Inventory+Management;Donors.+Hospitals.+Receivers.;Technology+with+a+Purpose." alt="Animated project introduction"/>

<br/><br/>

<img src="https://img.shields.io/badge/PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/FLASK-111827?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
<img src="https://img.shields.io/badge/SQLITE-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
<img src="https://img.shields.io/badge/STATUS-DEVELOPMENT-FF4D6D?style=for-the-badge" alt="Development status"/>

<br/><br/>

**A web-based blood bank management application designed to simplify blood inventory management, donor registration, and blood reservation workflows.**

[Explore Repository](https://github.com/tejassri-sm/Blood_Bank_Reservation_System) · [Report an Issue](https://github.com/tejassri-sm/Blood_Bank_Reservation_System/issues)

</div>

---

## `01` // PROJECT OVERVIEW

The **Blood Bank Reservation System** is a Python Flask web application that brings blood donors, receivers, hospitals, and administrators together through a centralized platform.

The system supports blood inventory management, reservation requests, donation records, and role-based access to help organize essential blood bank operations.

### 🎯 Project Objectives

- Simplify blood donation and reservation workflows.
- Maintain organized blood inventory records.
- Provide separate dashboards for different user roles.
- Support blood-group compatibility checks.
- Improve visibility into reservations and inventory status.

---

## `02` // KEY FEATURES

<table>
<tr>
<td width="50%" valign="top">

### 👨‍💼 Admin Dashboard

- Manage blood inventory.
- Monitor reservations and donation records.
- Review system activity.
- Access administrative functions.

</td>
<td width="50%" valign="top">

### 🩸 Donor Dashboard

- Access donor-related features.
- Manage donation information.
- Track donation history where available.
- Support donor eligibility workflows.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🏥 Hospital Dashboard

- Access hospital-related functionality.
- Work with blood reservation workflows.
- View relevant inventory and request information.

</td>
<td width="50%" valign="top">

### ❤️ Receiver Dashboard

- Access blood reservation features.
- Select the required blood group.
- Check compatible blood-group options.
- Follow the reservation workflow.

</td>
</tr>
</table>

### ⚡ Additional Functionality

- **Role-based access control** for protected pages.
- **Password hashing** using Werkzeug security utilities.
- **Session management** using Flask-Session.
- **Blood-group compatibility logic**, including a Bombay blood-group entry.
- **Reservation priority handling** and notification-related database models.

---

## `03` // TECHNOLOGY STACK

<div align="center">

<img src="https://skillicons.dev/icons?i=python,flask,sqlite,html,css,vscode,git,github&theme=dark" alt="Project technology stack"/>

</div>

| Technology | Purpose |
|---|---|
| Python | Application logic and backend development |
| Flask | Web framework and routing |
| Flask-SQLAlchemy | Database integration and ORM |
| SQLite | Persistent database storage |
| Flask-Session | Server-side session management |
| Werkzeug | Password hashing and security utilities |
| HTML5 | Web page structure |
| CSS3 | User interface styling |
| Git and GitHub | Version control and source management |

---

## `04` // SYSTEM ARCHITECTURE

```mermaid
flowchart TD
    A[User] --> B{User Role}
    B --> C[Admin]
    B --> D[Donor]
    B --> E[Hospital]
    B --> F[Receiver]

    C --> G[Flask Backend]
    D --> G
    E --> G
    F --> G

    G --> H[Authentication and Sessions]
    G --> I[Blood Inventory]
    G --> J[Reservation Management]
    G --> K[Donation Records]
    G --> L[Blood Compatibility Logic]

    H --> M[(SQLite Database)]
    I --> M
    J --> M
    K --> M
    L --> G
```

---

## `05` // PROJECT STRUCTURE

```text
Blood_Bank_Reservation_System/
│
├── app.py
├── blood_bank.py
├── models.py
├── requirements.txt
│
├── instance/
│   └── blood_bank.db
│
├── static/
│   └── css/
│       └── style.css
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── donor_dashboard.html
│   ├── hospital_dashboard.html
│   └── receiver_dashboard.html
│
└── README.md
```

---

## `06` // RUN LOCALLY

Follow these steps to run the application on your computer.

### Prerequisites

- Python 3.10 or later recommended.
- pip package manager.
- Git (optional, for cloning the repository).

### Step 1 — Clone the repository

```bash
git clone https://github.com/tejassri-sm/Blood_Bank_Reservation_System.git
cd Blood_Bank_Reservation_System
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Or, using Command Prompt:

```bat
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure the application

Before running the application, ensure the Flask secret key is configured securely using an environment variable and that the database initialization code is available.

**Security note:** Never use a development secret key in a public deployment. Keep production secrets out of source control.

### Step 5 — Start the application

The repository contains both `app.py` and `blood_bank.py`. Use the entry point that initializes the database and runs the Flask server. If `app.py` is configured as the main entry point, run:

```bash
python app.py
```

Open the local URL printed in your terminal, typically:

```text
http://127.0.0.1:5000/
```

> If the database tables have not been initialized, initialize them using the database setup supported by the project before opening the application.

---

## `07` // DATABASE MODELS

The application defines database models for its core workflows, including:

- **User** — user accounts and role information.
- **BloodInventory** — blood stock information.
- **Reservation** — blood reservation records.
- **DonationHistory** — donor-related records.
- **Notification** — notification-related data.

The application uses SQLite through Flask-SQLAlchemy.

---

## `08` // LEARNING OUTCOMES

Working on this project provides practical experience with:

- Building web applications using Flask.
- Connecting Python applications to a relational database.
- Implementing authentication and role-based authorization.
- Organizing application logic using database models.
- Managing sessions and user-specific dashboards.
- Developing workflows for inventory and reservation management.
- Structuring a multi-page web application.

---

## `09` // FUTURE ENHANCEMENTS

Potential improvements for future versions:

- Real-time blood stock availability.
- Email or SMS notifications.
- Advanced blood inventory analytics.
- Search and filtering by location and blood group.
- Improved reservation status tracking.
- Automated tests and stronger input validation.
- Deployment with production-grade security.
- Responsive interface improvements for mobile devices.

---

## `10` // CONTRIBUTIONS

Suggestions, bug reports, and improvements are welcome.

1. Fork this repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request describing your improvement.

---

<div align="center">

## 🩸 CODE WITH PURPOSE. BUILD TO SAVE LIVES.

**Developed by Tejas Sri S. M.**

<a href="https://github.com/tejassri-sm">
<img src="https://img.shields.io/badge/GITHUB-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub profile"/>
</a>

<br/><br/>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer&color=0:EF4444,55:7F1D1D,100:09090B" alt="Project footer"/>

<sub>DONATE BLOOD // SPREAD HOPE // SAVE LIVES</sub>

</div>
