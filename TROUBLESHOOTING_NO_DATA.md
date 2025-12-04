# Troubleshooting: No Bed/Alert Data on Dashboard

## Quick Checklist

### 1. Beds Must Exist in Database

The ESP8266 sends data with a `bed_id` (e.g., 1), but if that bed doesn't exist in the `beds` table, the data is rejected or ignored.

**Create beds via admin UI:**
1. Log in as admin
2. Go to **Settings** page
3. Look for a "Manage Beds" section (if available)

**OR directly in database (SQLite):**

Open a terminal and run:

```powershell
cd f:\Diwakar\new monitoring system
python -c "
import models
## Archived: TROUBLESHOOTING_NO_DATA.md

This troubleshooting guide was archived on 2025-12-04 and a copy is available at `archive/removed_files/TROUBLESHOOTING_NO_DATA.md`.

Original content removed from repo to declutter; archived copy retained.
"
