from datetime import date
from django.core.management.base import BaseCommand
from orders.models import Patient, Provider, Order, CarePlan


PATIENTS = [
    {"first_name": "Alice", "last_name": "Johnson", "mrn": "100001", "dob": date(1979, 6, 8)},
    {"first_name": "Bob", "last_name": "Williams", "mrn": "100002", "dob": date(1985, 3, 15)},
    {"first_name": "Carol", "last_name": "Davis", "mrn": "100003", "dob": date(1992, 11, 22)},
    {"first_name": "David", "last_name": "Martinez", "mrn": "100004", "dob": date(1968, 7, 30)},
    {"first_name": "Emily", "last_name": "Chen", "mrn": "100005", "dob": date(2001, 1, 5)},
]

PROVIDERS = [
    {"name": "Dr. Sarah Thompson", "npi": "1234567890"},
    {"name": "Dr. Michael Lee", "npi": "2345678901"},
    {"name": "Dr. Jennifer Park", "npi": "3456789012"},
]

ORDERS = [
    {
        "patient_mrn": "100001", "provider_npi": "1234567890",
        "medication_name": "IVIG",
        "primary_diagnosis": "G70.0 - Myasthenia gravis",
        "additional_diagnoses": "I10 - Hypertension, K21.0 - GERD",
        "medication_history": "Pyridostigmine 60mg q6h, Prednisone 10mg daily, Lisinopril 10mg daily",
        "patient_records": "Progressive proximal muscle weakness and ptosis over 2 weeks. AChR antibody positive. Neurology recommends IVIG.",
        "care_plan_status": "completed",
        "care_plan_content": """1. Problem List / Drug Therapy Problems (DTPs)
- Need for rapid immunomodulation to reduce myasthenic symptoms
- Risk of infusion-related reactions (headache, chills, nausea)
- Risk of renal dysfunction or volume overload with IVIG
- Risk of thromboembolic events
- Potential interaction: IVIG may reduce efficacy of live vaccines
- Patient education gap regarding infusion therapy

2. Goals (SMART)
- Primary: Achieve clinically meaningful improvement in MG-ADL score within 2-4 weeks
- Safety: Zero severe infusion reactions; no acute kidney injury (Cr stays within 0.3 mg/dL of baseline)
- Process: Complete full IVIG course (2 g/kg total dose over 2-5 days) with documented monitoring at each session

3. Pharmacist Interventions / Plan
- Dosing: IVIG 0.4 g/kg/day x 5 days (total 2 g/kg); for 72 kg patient = 28.8 g/day
- Premedication: Acetaminophen 650 mg PO + Diphenhydramine 25 mg PO, 30 min prior
- Infusion: Start at 0.5 mL/kg/hr, increase q30min by 0.5 mL/kg/hr to max 4 mL/kg/hr if tolerated
- Hydration: NS 250 mL bolus pre-infusion; encourage PO fluids 2-3 L/day
- Hold Lisinopril on infusion days if BP < 100/60

4. Monitoring Plan & Lab Schedule
- Pre-infusion: CBC, BMP (Cr, BUN), LFTs, baseline vitals
- Each infusion day: Vitals q15 min x4, then q30 min; assess for headache, flushing, dyspnea
- Post-course (Day 7): BMP to reassess renal function
- Week 2-4: Follow-up MG-ADL score, repeat AChR antibodies if clinically indicated""",
    },
    {
        "patient_mrn": "100002", "provider_npi": "2345678901",
        "medication_name": "Humira (adalimumab)",
        "primary_diagnosis": "M05.79 - Rheumatoid arthritis",
        "additional_diagnoses": "E11.9 - Type 2 diabetes",
        "medication_history": "Methotrexate 15mg weekly, Metformin 1000mg BID, Folic acid 1mg daily",
        "patient_records": "RA flare despite methotrexate. DAS28 score 5.1. Rheumatology recommends adding biologic therapy.",
        "care_plan_status": "completed",
        "care_plan_content": """1. Problem List / Drug Therapy Problems (DTPs)
- Inadequate RA disease control on methotrexate monotherapy
- Risk of serious infections (TB, hepatitis B reactivation) with biologic therapy
- Risk of injection site reactions
- Monitoring needed for hepatotoxicity (methotrexate + adalimumab)
- Diabetes management may be affected by RA inflammation control

2. Goals (SMART)
- Primary: Achieve DAS28 score < 3.2 (low disease activity) within 12 weeks
- Safety: No serious infections within first 6 months of therapy
- Process: Patient demonstrates correct self-injection technique by visit 2

3. Pharmacist Interventions / Plan
- Dosing: Adalimumab 40 mg SC every 2 weeks; continue methotrexate 15 mg weekly
- Pre-treatment screening: TB test (QuantiFERON), Hepatitis B panel, CBC, LFTs
- Patient education: Injection technique, storage (refrigerate 2-8°C), missed dose protocol
- Immunization review: Update pneumococcal, influenza, hepatitis B before starting; no live vaccines

4. Monitoring Plan & Lab Schedule
- Baseline: CBC, CMP, TB screening, Hep B panel, LFTs
- Month 1: CBC, LFTs, assess injection site reactions
- Every 3 months: CBC, CMP, DAS28 score, infection screening
- Annual: TB rescreening, LFTs""",
    },
    {
        "patient_mrn": "100003", "provider_npi": "1234567890",
        "medication_name": "Keytruda (pembrolizumab)",
        "primary_diagnosis": "C34.90 - Non-small cell lung cancer",
        "additional_diagnoses": "J44.1 - COPD",
        "medication_history": "Carboplatin/pemetrexed x4 cycles completed, Tiotropium 18mcg inhaled daily",
        "patient_records": "Stage IIIB NSCLC, PD-L1 TPS 60%. Completed first-line chemo, now maintenance immunotherapy.",
        "care_plan_status": "completed",
        "care_plan_content": """1. Problem List / Drug Therapy Problems (DTPs)
- Need for maintenance immunotherapy after first-line chemotherapy
- Risk of immune-related adverse events (colitis, hepatitis, pneumonitis, thyroiditis)
- COPD may mask early signs of immune-mediated pneumonitis
- Risk of infusion reactions
- Fatigue management during treatment

2. Goals (SMART)
- Primary: Maintain stable disease or achieve partial response on imaging at 9-week scan
- Safety: No grade 3+ immune-related adverse events within first 4 cycles
- Process: Patient recognizes and reports early signs of irAEs within 24 hours

3. Pharmacist Interventions / Plan
- Dosing: Pembrolizumab 200 mg IV q3 weeks; infuse over 30 min
- Pre-medication: Generally not required; dexamethasone only if prior infusion reaction
- irAE education: Provide wallet card listing symptoms to watch for (diarrhea, rash, cough, fatigue)
- COPD management: Continue tiotropium; low threshold for CT if new or worsening dyspnea

4. Monitoring Plan & Lab Schedule
- Each cycle (q3 weeks): CBC, CMP, TSH, LFTs, urinalysis, vitals
- Every 9 weeks: CT chest/abdomen/pelvis for restaging
- PRN: Cortisol level if fatigue worsens, pulmonary function tests if dyspnea""",
    },
    {
        "patient_mrn": "100001", "provider_npi": "1234567890",
        "medication_name": "Rituximab",
        "primary_diagnosis": "G70.0 - Myasthenia gravis",
        "additional_diagnoses": "I10 - Hypertension",
        "medication_history": "IVIG completed, Pyridostigmine 60mg q6h, Prednisone taper in progress",
        "patient_records": "Suboptimal response to IVIG. Neurology recommends rituximab for refractory MG.",
        "care_plan_status": "pending",
        "care_plan_content": "",
    },
    {
        "patient_mrn": "100004", "provider_npi": "3456789012",
        "medication_name": "Ocrevus (ocrelizumab)",
        "primary_diagnosis": "G35 - Multiple sclerosis",
        "additional_diagnoses": "F32.1 - Major depressive disorder",
        "medication_history": "Interferon beta-1a x2 years (discontinued for breakthrough activity), Sertraline 100mg daily",
        "patient_records": "Relapsing-remitting MS with 2 relapses in past year despite interferon. MRI shows new T2 lesions.",
        "care_plan_status": "processing",
        "care_plan_content": "",
    },
    {
        "patient_mrn": "100005", "provider_npi": "2345678901",
        "medication_name": "Dupixent (dupilumab)",
        "primary_diagnosis": "L20.9 - Atopic dermatitis",
        "additional_diagnoses": "J45.30 - Mild persistent asthma",
        "medication_history": "Topical triamcinolone 0.1%, Cetirizine 10mg daily, Albuterol PRN",
        "patient_records": "Severe atopic dermatitis, EASI score 28. Failed topical steroids and calcineurin inhibitors.",
        "care_plan_status": "failed",
        "care_plan_content": "Failed to generate care plan: API timeout after 30 seconds.",
    },
    {
        "patient_mrn": "100002", "provider_npi": "2345678901",
        "medication_name": "Ozempic (semaglutide)",
        "primary_diagnosis": "E11.9 - Type 2 diabetes",
        "additional_diagnoses": "E66.01 - Morbid obesity, I10 - Hypertension",
        "medication_history": "Metformin 1000mg BID, Lisinopril 20mg daily, Humira 40mg q2w",
        "patient_records": "A1C 8.2% despite max metformin. BMI 38. Endocrinology recommends GLP-1 RA.",
        "care_plan_status": "completed",
        "care_plan_content": """1. Problem List / Drug Therapy Problems (DTPs)
- Uncontrolled T2DM (A1C 8.2%) despite metformin monotherapy
- Obesity (BMI 38) contributing to insulin resistance
- Need for weight-favorable glucose-lowering agent
- GI side effects common with GLP-1 RA initiation
- Potential pancreatitis risk (low but requires monitoring)

2. Goals (SMART)
- Primary: Reduce A1C to < 7.0% within 6 months
- Secondary: Achieve 5-10% body weight reduction within 6 months
- Safety: No severe hypoglycemia; no signs of pancreatitis

3. Pharmacist Interventions / Plan
- Dosing: Semaglutide 0.25 mg SC weekly x4 weeks, then 0.5 mg weekly x4 weeks, then 1 mg weekly maintenance
- Continue metformin 1000 mg BID
- Patient education: Injection technique (abdomen, thigh, upper arm rotation), nausea management (eat smaller meals)
- Dietary counseling referral for diabetes-friendly meal planning

4. Monitoring Plan & Lab Schedule
- Baseline: A1C, lipid panel, renal function, amylase/lipase
- Month 1: Phone follow-up for GI tolerability, blood glucose log review
- Month 3: A1C, weight, renal function, assess for dose titration to 1 mg
- Month 6: A1C, comprehensive metabolic panel, lipid panel, weight""",
    },
]


class Command(BaseCommand):
    help = 'Seed database with mock patient, provider, order, and care plan data'

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing data...")
        CarePlan.objects.all().delete()
        Order.objects.all().delete()
        Patient.objects.all().delete()
        Provider.objects.all().delete()

        self.stdout.write("Creating providers...")
        provider_map = {}
        for p in PROVIDERS:
            provider = Provider.objects.create(**p)
            provider_map[p['npi']] = provider
            self.stdout.write(f"  + {provider}")

        self.stdout.write("Creating patients...")
        patient_map = {}
        for p in PATIENTS:
            patient = Patient.objects.create(**p)
            patient_map[p['mrn']] = patient
            self.stdout.write(f"  + {patient}")

        self.stdout.write("Creating orders and care plans...")
        for o in ORDERS:
            patient = patient_map[o['patient_mrn']]
            provider = provider_map[o['provider_npi']]

            order = Order.objects.create(
                patient=patient,
                provider=provider,
                medication_name=o['medication_name'],
                primary_diagnosis=o['primary_diagnosis'],
                additional_diagnoses=o['additional_diagnoses'],
                medication_history=o['medication_history'],
                patient_records=o['patient_records'],
            )

            CarePlan.objects.create(
                order=order,
                status=o['care_plan_status'],
                content=o['care_plan_content'],
            )

            self.stdout.write(f"  + Order #{order.id}: {order.medication_name} -> CarePlan ({o['care_plan_status']})")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {Patient.objects.count()} patients, "
            f"{Provider.objects.count()} providers, "
            f"{Order.objects.count()} orders, "
            f"{CarePlan.objects.count()} care plans."
        ))
