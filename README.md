# MiniSocial — Full Stack Social Media Web Application

![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/Vanilla_JS-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/CSS3-Modern_Responsive-1572B6?style=for-the-badge&logo=css3&logoColor=white)

MiniSocial is a modern full-stack social media application engineered strictly with **HTML5, CSS3, Vanilla JavaScript, Django, and SQLite**. The platform eliminates external frontend framework bloat while providing real-time database-driven interaction, granular privacy controls, community circles, and wellness-focused social mechanics.

---

## 📑 Table of Contents

- [Application Overview & Flow](#-application-overview--flow)
- [New Unique Features](#-new-unique-features)
- [Baseline Social Features](#-baseline-social-features)
- [Complete Application URL Routing](#-complete-application-url-routing)
- [Database Architecture & Models](#-database-architecture--models)
- [Security & Privacy Enforcement](#-security--privacy-enforcement)
- [Real-Time Polling Architecture](#-real-time-polling-architecture)
- [Directory Structure](#-directory-structure)
- [Installation & Setup](#-installation--setup)
- [Automated Verification & Tests](#-automated-verification--tests)

---

## 🗺️ Application Overview & Flow

The application follows an intentional authenticated flow with strict permission guards:

```
                            /
                            │
                            ▼
                     LANDING PAGE
                            │
                  ┌─────────┴─────────┐
                  │                   │
                  ▼                   ▼
               /login/            /register/
                  │                   │
                  └─────────┬─────────┘
                            ▼
                          /home/
                            │
     ┌──────────────┬───────┼───────┬──────────────┐
     │              │       │       │              │
     ▼              ▼       ▼       ▼              ▼
  /circles/    /explore/  FEED   /dashboard/   /settings/
     │              │       │       │
     ▼              ▼       ▼       ▼
 /circle/<id>/   #Topics  POSTS   METRICS
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
      POST DETAILS     POST EDIT       POST EVOLUTION
       & COMMENTS      (AUTHOR)           TIMELINE
```

---

## ✨ New Unique Features

### 1. 👥 MiniSocial Circles
Private and public interest-based micro-communities.
- **Roles:** `owner`, `admin`, and `member` with granular permissions.
- **Membership Management:** Owners and admins can add or remove members and promote members to admins. Normal members cannot remove the circle owner.
- **Discovery:** Browse and join public circles or private circles via direct membership.

### 2. 🔒 Post Visibility Controls & Circle Posts
Every post can be configured with one of four visibility scopes:
- `public` — Visible to all users across MiniSocial.
- `followers` — Restricted exclusively to approved followers of the author.
- `circle` — Strictly visible to verified members of a specific Circle.
- `private` — Accessible only by the author.
- **Backend-Enforced:** Unauthorized attempts to access `/post/<id>/` directly return **HTTP 403 Forbidden** with a custom security screen (`forbidden.html`).

### 3. 🎭 Mood-Based Feed & Mood Tagging
- **User Mood:** Select an active mood (😊 Happy, 🔥 Motivated, 🧘 Relaxed, 💻 Focused, 🌱 Learning, 🎨 Creative, 😌 Quiet). Saved to SQLite via `UserMood`.
- **Post Tagging:** Posts can optionally be tagged with an associated mood.
- **Dual Feed Modes:** Switch between **Normal Feed** (standard chronological algorithm) and **Mood Feed** (prioritizes posts tagged with the user's active mood).

### 4. ⏳ Post Expiry with Live Vanilla JS Countdowns
Authors can designate temporal lifespans for posts:
- **Lifetimes:** `1 Hour`, `6 Hours`, `24 Hours`, `3 Days`, `7 Days`, or `Permanent`.
- **Live Countdown:** Real-time ticking timer on expiring cards (`⏳ Expires in hh:mm:ss`).
- **Graceful Lifecycle:** Upon reaching zero, posts automatically fade from public streams. Authors retain access in their personal profile archive if enabled.

### 5. 📜 Post Evolution (Version History Timeline)
- When authors edit their posts, the previous content and timestamp are saved into the `PostVersion` table.
- Posts display a version badge (e.g. `v3 • View Evolution`).
- Clicking opens a timeline modal showing all previous revisions, edit timestamps, and progression history.

### 6. ❤️ Sentiment Reaction Reasons
Extends the Like system with optional reaction sentiments:
- `Helpful 👍`, `Funny 😂`, `Inspiring 🌟`, `Interesting 💡`, `Supportive 🤝`.
- Displays real aggregate reaction breakdown pills on each card calculated directly from SQLite.

### 7. 📊 Decision Posts / Polls
- Embed interactive decision polls with multiple options into posts.
- **Strict Integrity:** One vote per user enforced by SQLite unique constraints.
- **Real-Time Calculation:** Automatically computes dynamic vote counts and percentage bars.
- **Live Updates:** Non-intrusive polling updates percentages without full page reloads.

### 8. 🌿 Clean Feed Mode
A wellness-oriented toggle for distraction-free reading:
- When toggled **ON**, vanity engagement metrics (like counts, comment counts, follower counts) are hidden from the feed.
- Preserves author identity, content, media, and timestamps.
- Preference persists in SQLite via `UserPreference.clean_feed`.

### 9. 📈 Personal Social Dashboard (`/dashboard/`)
Private analytics portal strictly accessible by the logged-in user:
- Total Posts, Total Comments, Likes Received, Likes Given.
- Follower count, Following count, Circle memberships.
- Weekly activity velocity (posts this week, comments this week, follower growth).
- Real SQL aggregation using Django ORM (`Count`, `filter`, `annotate`).

### 10. 🎯 Daily Social Missions
Daily community challenges designed to encourage positive social habits:
- *"Share something you learned today"*, *"Leave a helpful comment"*, *"Participate in a poll"*, *"Support a useful post"*.
- Automatically marks completed in SQLite when the user triggers the corresponding action.

### 11. 🏷️ Topic & Interest System (`/explore/`)
- Automatic hashtag extraction from post captions (`#Python`, `#Django`, `#WebDev`).
- Interactive **Explore Page** displaying popular topics, topic post counts, and personal interest bookmarks.
- Feed prioritizes content matching selected user interests.

### 12. 🔍 Multi-Entity Global Search (`/search/`)
Search across all database entities simultaneously:
- **Users:** Match by username or bio.
- **Posts:** Match by caption or text content.
- **Circles:** Match by circle name or description.
- **Topics:** Match by topic hashtags.

---

## 🏛️ Baseline Social Features

MiniSocial maintains all foundational features in complete working order:
- **Landing Page (`/`):** Responsive marketing landing page with hero banner, feature highlights, and login/register calls-to-action.
- **Authentication:** Registration, login, password changes, and logout with CSRF protection and Django session authentication.
- **User Profiles:** Custom avatar uploads, bio updates, fallback dynamic SVG avatars with customizable accent colors.
- **Social Graph:** Follow / unfollow with database-level constraints preventing self-following or duplicate records.
- **Interactive Feed:** Infinite scroll / polling feed, image uploads with client-side preview and remove controls.
- **Notifications System:** In-app notifications for likes, comments, follows, and circle invitations with real-time badge updates and mark-as-read triggers.
- **Direct Messaging:** One-to-one conversational messaging with conversation list, message threads, and polling updates.

---

## 🗺️ Complete Application URL Routing

| Route | View Method | Description | Access |
|---|---|---|---|
| `/` | `landing_view` | Public Landing Page | Public |
| `/login/` | `login_view` | User Login | Public |
| `/register/` | `register_view` | User Registration | Public |
| `/logout/` | `logout_view` | Session Termination (Redirects to `/`) | Authenticated |
| `/home/` | `home_view` | Main Feed (Supports `?feed=mood` & `?topic=...`) | Authenticated |
| `/profile/` | `profile_view` | Authenticated User Profile | Authenticated |
| `/user/<username>/` | `user_profile_view` | Public Profile of Other Users | Authenticated |
| `/post/<id>/` | `post_detail_view` | Post Detail with Comments & Polls | Authenticated (Permission Checked) |
| `/circles/` | `circles_view` | Circles Discovery & Create Modal | Authenticated |
| `/circle/<id>/` | `circle_detail_view` | Circle Page with Feed & Member Manager | Authenticated (Member Restricted) |
| `/circle/create/` | `create_circle_view` | Create Circle Endpoint (POST) | Authenticated |
| `/circle/<id>/join/` | `join_circle_view` | Join Circle Endpoint (POST) | Authenticated |
| `/circle/<id>/leave/` | `leave_circle_view` | Leave Circle Endpoint (POST) | Authenticated |
| `/circle/<id>/members/` | `manage_circle_members_view`| Admin Member Role & Removal (POST) | Circle Admin/Owner |
| `/dashboard/` | `dashboard_view` | Private Personal Analytics Dashboard | Authenticated (Self Only) |
| `/explore/` | `explore_view` | Topics Exploration & Post Discovery | Authenticated |
| `/interests/update/` | `update_interests_view`| Bookmark/Remove User Topics (POST) | Authenticated |
| `/user/mood/` | `update_mood_view` | Update Current User Mood (POST) | Authenticated |
| `/preferences/update/`| `update_preferences_view`| Update Feed Preferences & Clean Feed | Authenticated |
| `/missions/` | `daily_missions_view` | Fetch Active Daily Missions (GET) | Authenticated |
| `/mission/<id>/complete/`| `complete_mission_view` | Complete Daily Mission (POST) | Authenticated |
| `/search/` | `search_view` | Multi-Entity Search Query (`?q=...`) | Authenticated |
| `/post/create/` | `create_post_view` | Publish Post with Expiry/Mood/Poll | Authenticated |
| `/post/<id>/edit/` | `post_edit_view` | Edit Post & Archive Version (POST) | Post Author |
| `/post/<id>/versions/` | `post_versions_view` | Get Version History Timeline (GET) | Authenticated |
| `/post/<id>/like/` | `like_post_view` | Like / Unlike with Reaction Reason | Authenticated |
| `/poll/<id>/vote/` | `poll_vote_view` | Cast Vote on Poll Option (POST) | Authenticated (1 Vote Max) |
| `/notifications/` | `notifications_view` | View Notification Stream | Authenticated |
| `/messages/` | `messages_view` | Direct Messaging Dashboard | Authenticated |
| `/settings/` | `settings_view` | Account, Profile, and Feed Settings | Authenticated |

---

## 🗄️ Database Architecture & Models

```
┌──────────────────┐           ┌──────────────────┐
│       User       │◀──────────│     Profile      │
└─────────┬────────┘           └──────────────────┘
          │
          ├─────────────────────────────┬─────────────────────────────┐
          ▼                             ▼                             ▼
┌──────────────────┐           ┌──────────────────┐          ┌──────────────────┐
│      Circle      │           │       Post       │          │   UserPreference │
├──────────────────┤           ├──────────────────┤          ├──────────────────┤
│ owner (FK User)  │           │ author (FK User) │          │ clean_feed (bool)│
│ name (CharField) │           │ circle (FK Circle│          │ preferred_mood   │
│ is_private (bool)│           │ visibility (enum)│          │ show_expired_post│
└─────────┬────────┘           │ mood (CharField) │          └──────────────────┘
          │                    │ expires_at (dt)  │
          ▼                    └────────┬─────────┘
┌──────────────────┐                    │
│   CircleMember   │                    ├────────────────┬────────────────┐
├──────────────────┤                    ▼                ▼                ▼
│ circle (FK)      │          ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│ user (FK)        │          │  PostVersion   │ │     Like     │ │     Poll     │
│ role (owner/adm) │          ├────────────────┤ ├──────────────┤ ├──────────────┤
└──────────────────┘          │ version_number │ │ reason (enum)│ │ question     │
                              │ content        │ └──────────────┘ └──────┬───────┘
                              └────────────────┘                         │
                                                                         ▼
                                                                ┌────────────────┐
                                                                │   PollOption   │
                                                                └────────┬───────┘
                                                                         │
                                                                         ▼
                                                                ┌────────────────┐
                                                                │    PollVote    │
                                                                ├────────────────┤
                                                                │ (poll, user)   │
                                                                │ UNIQUE         │
                                                                └────────────────┘
```

### Key Models Defined in `backend/social/models.py`:
1. **`Profile`**: Extends Django's `User` with bio, avatar picture upload, fallback color, and created timestamp.
2. **`Post`**: Core content unit extended with `visibility`, `circle` foreign key, `mood`, `expires_at`, and `version_count`.
3. **`PostVersion`**: Retains full snapshots of previous post iterations for the evolution timeline.
4. **`Circle` & `CircleMember`**: Manages groups, descriptions, and membership roles with `unique_together = ('circle', 'user')`.
5. **`Poll`, `PollOption`, `PollVote`**: Manages decision posts, dynamic vote counts, and prevents duplicate voting via `unique_together = ('poll', 'user')`.
6. **`UserMood`**: Stores the user's active emotional/intent state in SQLite.
7. **`UserPreference`**: Stores clean feed toggles, preferred mood defaults, and archive visibility settings.
8. **`DailyMission` & `UserMission`**: Manages community engagement missions and tracks completion per user.
9. **`Topic`, `PostTopic`, `UserInterest`**: Manages hashtag indexing and user topic subscriptions.
10. **`Like`, `Comment`, `Follow`, `Notification`, `Conversation`, `Message`**: Core interaction records with database-level uniqueness constraints.

---

## 🛡️ Security & Privacy Enforcement

- **Backend-Driven Authorization:** Permissions are checked directly in Django views. The frontend does not determine authorization.
- **Private Circle Access Control:** Attempts to access posts belonging to private circles by non-members trigger an immediate HTTP 403 Forbidden with custom error template.
- **Author-Only Editing:** Post edits are verified against `request.user == post.author`. Non-authors receive HTTP 403.
- **Duplicate Prevention:**
  - Duplicate follows prevented by `unique_follower_following` constraint and `prevent_self_follow` check constraint.
  - Duplicate likes prevented by `unique_user_post_like`.
  - Duplicate circle joins prevented by `unique_circle_user`.
  - Duplicate poll votes prevented by `unique_poll_user_vote`.
  - Duplicate topic tags and mission completions are prevented at the database level.
- **CSRF Protection:** All AJAX requests extract and send the Django CSRF token via headers (`X-CSRFToken`).

---

## ⚡ Real-Time Polling Architecture

MiniSocial utilizes a non-blocking Vanilla JavaScript polling architecture:
- **Feed Updates (`/feed/updates/?after=<id>`):** Polls every 4–5 seconds to fetch new posts prependable to the feed stream without reloading the page.
- **Notifications Badge (`/notifications/updates/`):** Polls every 3–5 seconds to dynamically update unread count badges.
- **Direct Messages (`/messages/<id>/updates/`):** Polls every 2–3 seconds while in an active chat window.
- **Poll Live Updates (`/poll/<id>/updates/`):** Refreshes vote percentages without DOM interruption.
- **Overlapping Request Guard:** Each polling function features an active request lock flag (`isPolling = true`) preventing queued duplicate calls on slow connections.

---

## 📁 Directory Structure

```
MiniSocialMediaApp/
├── backend/
│   ├── manage.py
│   ├── minisocial/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── social/
│       ├── models.py              # All 15+ SQLite models & constraints
│       ├── views.py               # Complete business logic & API handlers
│       ├── urls.py                # Application URL routing
│       ├── admin.py               # Django Admin model registrations
│       ├── forms.py               # Django forms
│       ├── context_processors.py  # Global context (notifications/messages)
│       └── migrations/            # Django database migrations
│
├── database/
│   └── db.sqlite3                 # Live SQLite database file
│
├── frontend/
│   ├── templates/                 # Production Django HTML5 templates
│   │   ├── landing.html           # Public landing page
│   │   ├── login.html             # Login view
│   │   ├── register.html          # Registration view
│   │   ├── home.html              # Main feed with moods, missions & polls
│   │   ├── circles.html           # Circles discovery & creation
│   │   ├── circle_detail.html     # Circle feed & member management
│   │   ├── dashboard.html         # Personal analytics dashboard
│   │   ├── explore.html           # Topic exploration & interests
│   │   ├── search.html            # Multi-entity search
│   │   ├── profile.html           # User profile
│   │   ├── user_profile.html      # Other user profile
│   │   ├── post_detail.html       # Single post details & comment stream
│   │   ├── notifications.html     # Notification list
│   │   ├── messages.html          # Real-time messages view
│   │   ├── settings.html          # Account & feed preferences
│   │   └── forbidden.html         # 403 Access denied screen
│   │
│   └── static/                    # Static assets
│       ├── css/                   # Vanilla CSS stylesheets
│       │   ├── new-features.css   # Styles for circles, polls, dashboard
│       │   ├── home.css           # Home layout & feed cards
│       │   ├── landing.css        # Landing page styling
│       │   ├── settings.css       # Settings styling
│       │   └── ...
│       └── js/                    # Vanilla JavaScript modules
│           ├── home.js            # Feed interactions, polls & expiry
│           ├── settings.js        # Preference updates & avatar changes
│           ├── messages.js        # Real-time chat polling
│           └── ...
│
├── media/                         # User-uploaded images & avatars
├── test_integration.py            # Baseline 13-point integration test suite
├── test_new_features.py           # Automated test suite for all 12 new features
├── populate_db.py                 # Sample database seeder
├── requirements.txt               # Dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/ybhargavi40021978-alt/MiniSocialMediApp.git
cd MiniSocialMediApp
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. (Optional) Seed Sample Data
```bash
python populate_db.py
```
> **Sample Accounts:**
> - Usernames: `bhargavi`, `sai_kumar`, `priya`, `rahul`, `ananya`, `teja`, `vikas`, `neha`
> - Default Password: `password123`

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

## 🧪 Automated Verification & Tests

The project includes two end-to-end automated test suites.

### 1. Verify All 12 New Features:
```bash
python test_new_features.py
```
**Test Coverage:**
- ✅ Circle creation, member joining, member count updating, duplicate join rejection.
- ✅ Post visibility scopes (`public`, `followers`, `circle`, `private`) with HTTP 403 enforcement.
- ✅ User mood selection, persistence, and mood-prioritized feed filtering.
- ✅ Post expiry scheduling, live countdown math, and feed disappearance.
- ✅ Post evolution version snapshotting in `PostVersion` and unauthorized edit prevention.
- ✅ Like sentiment reasons (Helpful, Funny, Inspiring) with breakdown metrics.
- ✅ Decision poll creation, single-vote enforcement, and real-time percentage math.
- ✅ Clean Feed mode persistence and DOM class toggling.
- ✅ Personal Social Dashboard privacy and SQL metric calculations.
- ✅ Daily Mission auto-completion and duplicate prevention.
- ✅ Topic tagging, user interest subscription, and Explore discovery.
- ✅ Multi-entity search across Users, Posts, Circles, and Topics.

### 2. Verify Baseline Features:
```bash
python test_integration.py
```
**Test Coverage:**
- ✅ Registration, Login, Logout, Profile Picture upload, Bio update, Follow/Unfollow, Posts with images, Likes, Comments, Direct Messaging, and Notifications.

---

## 📄 License
This project is licensed under the MIT License.
