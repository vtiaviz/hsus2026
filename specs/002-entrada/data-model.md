# Data Model: Entrada (M2)

| Model | App | Campos principais | Relações e regras |
| --- | --- | --- | --- |
| `Patient` | patients | `cns`, `cpf` (únicos, opcionais, pelo menos um), `medical_record_number` (único), `name`, `mother_name`, `sex` (M/F), `race` (01–05, 99), `birth_date`, `phone`, `street_type`, `street`, `number`, `complement`, `neighborhood`, `zipcode` | `Municipality` (PROTECT), `created_by` |
| `PatientAccessLog` | patients | `accessed_at`, `view_name` | `Patient`, `User`, `CareSession` (PROTECT) |
| `CareSession` | reception | `origin` (new, transfer), `transfer_destination` (ambulatory, infirmary, diagnostic_exam, telemedicine), `status`, `arrived_at`, `complaint`, `finished_at` | `Patient`, `Establishment`, `created_by`; um aberto por paciente |
| `Triage` | reception | `systolic`, `diastolic`, `temperature`, `heart_rate`, `oxygen_saturation`, `has_allergy`, `allergy_description`, `risk` (low, medium, high, very_high), `recorded_at` | 1:1 `CareSession`, `recorded_by` |
| `Consultation` | reception | `kind` (entry, transfer), `diagnosis`, `care_plan`, `referral` (ambulatory, infirmary, discharge), `recorded_at` | 1:1 `CareSession`, `physician`, `Cid10`, `recorded_by` |
| `Medication` | clinical | `name` (único), `is_active` | catálogo do admin |
| `ExamType` | clinical | `name` (único), `is_active` | catálogo; sete tipos por migração |
| `PrescribedMedication` | clinical | `dosage`, `form`, `route`, `times`, `interval_hours` (6, 8, 12, 24), `duration`, `duration_unit` (day, week, month); `posology` | `CareSession`, `Consultation`, `Medication` |
| `ExamRequest` | clinical | `external_id` (LabSUS), `requested_at` | `CareSession`, `Consultation` (opcional), `ExamType`, `requested_by` |
| `MedicalCertificate` | clinical | `days`, `issued_at` | 1:1 `CareSession`, `Cid10` (opcional), `physician` |

Todas as FKs são `PROTECT`.
