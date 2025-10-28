# K9 Operations Data Seeding Tool

An interactive command-line tool to populate your K9 Operations database with realistic test data.

## Features

- ✅ **Idempotent** - Safe to run multiple times, skips existing records
- 🔄 **Interactive Menu** - Choose which models to seed or seed everything at once  
- 🇸🇦 **Realistic Arabic Data** - Authentic names, locations, and descriptions
- 🔗 **Proper Relationships** - Maintains foreign key integrity across all models
- 🛡️ **Safety Checks** - Automatic enum validation and confirmation for destructive operations

## Quick Start

### Seed Everything (Recommended for first run)

```bash
python seed_data.py
```

Then select option **99** to seed all models at once.

### Interactive Mode

Run the script and choose specific models to populate:

```bash
python seed_data.py
```

Available options:
- **1-4**: Core entities (Users, Employees, Dogs, Projects)
- **5-8**: Operations (Training, Veterinary, Breeding, Shifts)
- **9-12**: Daily management (Schedules, Reports, Logs, Tasks)
- **13**: System settings
- **99**: Seed everything
- **-1**: Clear all data (⚠️ DANGER ZONE)

## Default Data Volumes

When you select option 99 (Seed All), the following amounts are created:

| Model | Count | Description |
|-------|-------|-------------|
| Users | 15 | Admin, Project Managers, Handlers |
| Employees | 25 | Trainers, Vets, Breeders, etc. |
| Dogs | 40 | K9 units with various breeds |
| Projects | 10 | Security operations |
| Training Sessions | 60 | Dog training records |
| Veterinary Visits | 50 | Health checkups |
| Breeding Operations | 12 | Heat cycles, mating, puppies |
| Daily Schedules | 15 | Handler assignments |
| Handler Reports | 30 | Daily reports with all sections |
| Caretaker Logs | 40 | Feeding, grooming, etc. |
| Tasks & Notifications | 20 | System tasks |

## Default Login Credentials

After seeding, you can login with:

- **Username**: `admin`
- **Password**: `password123`
- **Role**: GENERAL_ADMIN

Additional test users:
- `pm_1`, `pm_2`, `pm_3` (PROJECT_MANAGER role)
- `handler_4` through `handler_14` (HANDLER role)

All test accounts use password: `password123`

## Customizing Data Volumes

When running interactively, you can specify custom counts for each model:

```bash
python seed_data.py
# Select option 1 (Users)
# Enter: 20  (creates 20 users instead of default 10)
```

## Data Characteristics

### Arabic Names & Data
- Employee and user names use authentic Arabic names
- Project names reflect real security operations
- All descriptions and notes are in Arabic

### Realistic Relationships
- Employees are assigned roles (Trainers, Vets, Handlers, etc.)
- Dogs are assigned specializations (Explosives, Drugs, Attack, etc.)
- Training sessions link trainers with dogs
- Breeding records track complete lineage (mother, father, puppies)
- Handler reports include all sections (health, training, care, behavior)

### Dates & Timing
- Historical data spans the last 30-365 days
- Breeding cycles follow realistic timing (63-day pregnancy)
- Daily schedules cover recent dates
- Future dates used for project end dates and task due dates

## Safety Features

### Automatic Enum Checking
The script automatically checks if the `HANDLER` role exists in the database enum and adds it if missing.

### Idempotent Creation
All core entities check for existing records before creating new ones:
- Users checked by `username`
- Employees checked by `employee_id`
- Dogs checked by `code`
- Projects checked by `code`

This means you can safely run the script multiple times without creating duplicates.

### Clear Data Protection
The `-1` option to clear all data requires typing `DELETE ALL` to confirm, preventing accidental data loss.

## Troubleshooting

### "IntegrityError: duplicate key value violates unique constraint"

This should no longer occur with the idempotent fixes, but if you see it:
1. The script will skip existing records automatically
2. Or use option `-1` to clear all data first (⚠️ WARNING: This deletes everything)

### "invalid input value for enum userrole: HANDLER"

The script now automatically fixes this by adding the missing enum value.

### Need to Start Fresh?

```bash
python seed_data.py
# Select -1
# Type: DELETE ALL
# Then select 99 to reseed everything
```

## Development Notes

- Script requires an active Flask app context
- Uses UUID primary keys for all models
- Maintains foreign key integrity through proper ordering
- Creates data in dependency order (users → employees → dogs → projects → etc.)

## Contributing

When adding new models to seed:
1. Add a `seed_model_name()` method to the DataSeeder class
2. Add idempotent checking for unique fields
3. Add the option to the interactive menu
4. Include the call in `seed_all()` method

## Support

For issues or questions, refer to the main K9 Operations documentation.
