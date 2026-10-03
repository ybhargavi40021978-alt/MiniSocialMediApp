# MiniSocial — Full Stack Web Application

MiniSocial is a complete social media web application built with **HTML5, CSS3, Vanilla JavaScript, Django, and SQLite**. The project architecture strictly separates **frontend**, **backend**, and **database** logic while keeping the approved UI design and interactive behavior 100% intact.

---

## 🗺️ Application Page Flow

```
                    /
                    │
                    ▼
             LANDING PAGE
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
       LOGIN               REGISTER
          │                   │
          └─────────┬─────────┘
                    ▼
                  HOME
                    │
       ┌────────────┼─────────────┐
       │            │             │
       ▼            ▼             ▼
    PROFILE       CREATE        NOTIFICATIONS
                   POST
       │            │
       ▼            ▼
 USER PROFILE    POST DETAILS
       │            │
       ├────────────┤
       │            │
       ▼            ▼
   FOLLOW       LIKE / COMMENT
       │
       ▼
 FOLLOWERS / FOLLOWING
```

---

## 🏗️ Project Architecture

```
MiniSocialMediaApp/
│
├── frontend/
│   ├── templates/
│   │   ├── landing.html            # Public Landing Page (Served at "/")
│   │   ├── register.html           # Screen 1: Registration
│   │   ├── login.html              # Screen 2: Login
│   │   ├── home.html               # Screen 3 & 9: Home Feed + Create Post Modal
│   │   ├── profile.html            # Screen 4: Current User Profile
│   │   ├── user_profile.html       # Screen 5: Other User Profile
│   │   ├── post_details.html       # Screen 6: Post Details with Comments
│   │   ├── notifications.html      # Screen 7: Notifications list
│   │   ├── followers.html          # Screen 8: Followers Dashboard
│   │   ├── following.html          # Screen 8: Following Dashboard
│   │   ├── create_post.html        # Screen 9: Standalone modal view
│   │   ├── like_unlike.html        # Screen 10: Like/Unlike UI State screen
│   │   └── follow_unfollow.html    # Screen 11: Follow/Unfollow UI State screen
│   │
│   └── static/
│       ├── css/
│       │   ├── landing.css
│       │   ├── style.css
│       │   ├── home.css
│       │   ├── profile.css
│       │   ├── user-profile.css
│       │   ├── post-detail.css
│       │   ├── notifications.css
│       │   ├── followers.css
│       │   ├── create-post.css
│       │   ├── like-unlike.css
│       │   └── follow-unfollow.css
│       │
│       ├── js/
│       │   ├── landing.js
│       │   ├── main.js
│       │   ├── login.js
│       │   ├── home.js
│       │   ├── profile.js
│       │   ├── user-profile.js
│       │   ├── post-detail.js
│       │   ├── notifications.js
│       │   ├── followers.js
│       │   ├── create-post.js
│       │   ├── like-unlike.js
│       │   └── follow-unfollow.js
│       │
│       ├── images/
│       └── uploads/
│
├── backend/
│   ├── manage.py
│   ├── minisocial/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── social/
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── forms.py
│       ├── admin.py
│       ├── context_processors.py
│       └── migrations/
│
├── database/
│   ├── db.sqlite3
│   └── migrations/
│
├── manage.py
├── populate_db.py
├── test_integration.py
├── requirements.txt
└── README.md
```

---

## 🔒 Duplicate Data Prevention & Integrity

1. **Unique Constraints (Database Level)**:
   - `Like`: `UniqueConstraint(fields=['user', 'post'], name='unique_user_post_like')`
   - `Follow`: `UniqueConstraint(fields=['follower', 'following'], name='unique_follower_following')`
   - `Self-Follow`: `CheckConstraint(condition=~models.Q(follower=models.F('following')), name='prevent_self_follow')`
2. **Double-Click & Rapid Submission Protection (View Level)**:
   - `like_post_view`: Uses `get_or_create` and toggles cleanly.
   - `follow_user_view`: Uses `get_or_create` and toggles cleanly.
   - `comment_post_view`: Checks for recent identical comment submissions by the same user to prevent accidental double submissions.
   - `create_post_view`: Prevents rapid duplicate post creation.
   - `Notification`: Automatically de-duplicates unread notifications for follow and like actions.

---

## 🚀 Installation & Setup Guide

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows (Command Prompt / PowerShell)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Populate Sample Test Data (Optional Developer Fixture)
```bash
python populate_db.py
```
> **Default Test Credentials for All Sample Users**:
> - Password: `password123`
> - Sample Accounts: `bhargavi`, `sai_kumar`, `priya`, `rahul`, `ananya`, `teja`, `vikas`, `neha`

### 5. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
You can run the server from the root directory OR from the `backend/` directory:
```bash
# Option A (From project root):
python manage.py runserver

# Option B (From backend/):
cd backend
python manage.py runserver
```
Open your browser at **`http://127.0.0.1:8000/`**.

---

## 🧪 Run Automated Integration Tests
```bash
python test_integration.py
```
> Validates all 15 key user flows and checks duplicate prevention:
> `[PASS] 1. Root URL '/' serves the MiniSocial Landing Page`
> `[PASS] 2. Protected page /home/ correctly redirects unauthenticated user to /login/`
> `[PASS] 3. Registration Page loads at /register/`
> `[PASS] 4. Registration creates user in DB and establishes session at /home/`
> `[PASS] 5. Create Post works on Home feed (Created Post #12)`
> `[PASS] 6. Like works (Count = 1)`
> `[PASS] 7. Unlike works (Count = 0)`
> `[PASS] 8. Comment works (Count = 1)`
> `[PASS] 9. View Other User Profile works`
> `[PASS] 10. Follow / Unfollow toggle works`
> `[PASS] 11. Followers & Following views load correctly`
> `[PASS] 12. Notifications view loads correctly`
> `[PASS] 13. Current User Profile loads correctly`
> `[PASS] 14. Logout redirects back to MiniSocial Landing Page ('/')`
> `[PASS] 15. Login again succeeds and previously created database records persist`

---

## 🗺️ Application URL Map
| URL | Description |
| --- | --- |
| `/` | Public MiniSocial Landing Page (Hero, Features, How it works, Footer) |
| `/register/` | User Registration Page (Screen 1) |
| `/login/` | User Login Page (Screen 2) |
| `/logout/` | User Logout (Redirects to `/`) |
| `/home/` | Home / Feed Page with Create Post modal (Screens 3 & 9) |
| `/profile/` | Current User Profile Page (Screen 4) |
| `/user/<username>/` | View Another User Profile Page (Screen 5) |
| `/post/<id>/` | Post Detail Page with Comments (Screen 6) |
| `/notifications/` | Notifications Page (Screen 7) |
| `/followers/` | Followers Dashboard (Screen 8) |
| `/following/` | Following Dashboard (Screen 8) |
| `/demo/like-unlike/` | Like / Unlike UI State Screen (Screen 10) |
| `/demo/follow-unfollow/` | Follow / Unfollow UI State Screen (Screen 11) |
| `/admin/` | Django Administration Panel |
