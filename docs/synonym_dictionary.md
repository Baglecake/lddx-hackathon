# LDDx Clinical Synonym Dictionary

> **Purpose:** This dictionary maps clinically equivalent diagnosis terms
> used by the LDDx evaluation pipeline. When the pipeline produces a
> diagnosis that differs in wording from the ground truth, these mappings
> determine whether it counts as a match.
>
> **For reviewers:** Please verify existing mappings and add any missing
> synonyms. Each group lists a **canonical term** (the ground truth label
> from Open-XDDx) followed by its accepted **aliases** (terms the pipeline
> might produce that should count as equivalent).
>
> **How to contribute:** Add new terms to the alias column, or create new
> rows. If unsure about a mapping, prefix with `?` (e.g., `?angina`).

---

## Part 1: Synonym Groups

### Cardiovascular

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **myocardial infarction** | acute mi, heart attack, mi |
| 2 | **acute coronary syndrome** | acs |
| 3 | **congestive heart failure** | cardiac failure, chf, heart failure |
| 4 | **atrial fibrillation** | af, afib |
| 5 | **carotid sinus syndrome** | carotid sinus hypersensitivity, carotid sinus syncope |

### Renal

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **acute kidney injury** | acute renal failure, aki, arf |
| 2 | **chronic kidney disease** | chronic renal failure, ckd, crf |
| 3 | **contrast-induced nephropathy** | cin, contrast nephropathy, contrast-induced aki |
| 4 | **acute nephropyelitis** | acute pyelonephritis, kidney infection, pyelonephritis, upper urinary tract infection |
| 5 | **chronic nephropyelitis** | chronic pyelonephritis, recurrent pyelonephritis |
| 6 | **renal tuberculosis** | genitourinary tuberculosis, tuberculosis of kidney, urogenital tuberculosis |
| 7 | **bladder stones** | bladder calculi, cystolithiasis, urinary bladder stones, vesical calculi |

### Respiratory

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **chronic obstructive pulmonary disease** | copd |
| 2 | **community-acquired pneumonia** | cap, pneumonia |
| 3 | **acute respiratory distress syndrome** | ards |
| 4 | **pulmonary embolism** | pe |
| 5 | **deep vein thrombosis** | dvt |

### Endocrine

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **diabetes mellitus** | diabetes, dm |
| 2 | **diabetic ketoacidosis** | dka |
| 3 | **type 1 diabetes** | iddm, t1dm |
| 4 | **type 2 diabetes** | niddm, t2dm |

### Hematology

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **thrombotic thrombocytopenic purpura** | ttp |
| 2 | **thrombotic microangiopathy** | tma |
| 3 | **disseminated intravascular coagulation** | dic |
| 4 | **hemolytic uremic syndrome** | hus |
| 5 | **hemolytic anemia** | ha |
| 6 | **microangiopathic hemolytic anemia** | maha, microangiopathic ha |
| 7 | **autoimmune hemolytic anemia** | aiha, autoimmune ha |
| 8 | **paroxysmal nocturnal hemoglobinuria** | pnh |
| 9 | **sickle cell disease** | scd, sickle cell anemia |
| 10 | **iron deficiency anemia** | ida, iron deficiency |
| 11 | **megaloblastic anemia** | b12 deficiency, folate deficiency |
| 12 | **spherocytosis** | hereditary spherocytosis |
| 13 | **thrombocytopenia** | low platelets |
| 14 | **immune thrombocytopenic purpura** | idiopathic thrombocytopenic purpura, itp |
| 15 | **heparin induced thrombocytopenia** | hit |
| 16 | **antiphospholipid syndrome** | antiphospholipid antibody syndrome, aps |

### Rheumatology

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **systemic lupus erythematosus** | lupus, sle |
| 2 | **rheumatoid arthritis** | ra |
| 3 | **ankylosing spondylitis** | as |
| 4 | **pseudogout** | calcium pyrophosphate deposition disease, calcium-pyrophosphate disease, chondrocalcinosis, cppd, cppd arthropathy, cppd deposition disease |
| 5 | **gout** | gouty arthritis, uric acid arthropathy |
| 6 | **osteoarthritis** | degenerative joint disease, oa |
| 7 | **disseminated gonorrhea** | disseminated gonococcal infection, gonococcal arthritis, reactive arthritis |
| 8 | **reiter syndrome (reactive arthritis)** | reactive arthritis, reiter disease, reiter syndrome |

### Infectious

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **pneumocystis jirovecii pneumonia** | pcp, pjp, pneumocystis jiroveci pneumonia, pneumocystis pneumonia |
| 2 | **allergic bronchopulmonary aspergillosis** | abpa, allergic aspergillosis |
| 3 | **acute pulmonary aspergillosis** | aspergillus pneumonia, invasive aspergillosis |
| 4 | **histoplasmosis** | histo, histoplasma infection |
| 5 | **coccidioidomycosis** | cocci, valley fever |
| 6 | **tuberculosis** | pulmonary tuberculosis, tb |

### Neurology

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **transient ischemic attack** | tia |
| 2 | **cerebrovascular accident** | cva, stroke |
| 3 | **multiple sclerosis** | ms |

### Gastroenterology

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **gastroesophageal reflux disease** | gerd |
| 2 | **inflammatory bowel disease** | ibd |
| 3 | **peptic ulcer disease** | pud |
| 4 | **infectious gastroenteritis** | bacterial gastroenteritis, gastroenteritis, viral gastroenteritis |

### Infectious Disease

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **urinary tract infection** | uti |
| 2 | **acquired immunodeficiency syndrome** | aids |
| 3 | **human immunodeficiency virus** | hiv |

### Movement Disorders / Psychiatry

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **pseudoparkinsonism** | antipsychotic-induced parkinsonism, drug-induced parkinsonism, neuroleptic-induced parkinsonism |
| 2 | **tardive dyskinesia** | oral-facial dyskinesia, orofacial dyskinesia |
| 3 | **neuroleptic malignant syndrome** | nms |
| 4 | **akathisia** | drug-induced akathisia, neuroleptic-induced akathisia |

### Cardiovascular (extended)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **cardiac contusion** | blunt cardiac injury, myocardial contusion |
| 2 | **vasovagal syncope** | neurocardiogenic syncope, vasovagal episode, vasovagal reaction |

### Headache

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **tension headache** | tension type headache, tension-type headache |
| 2 | **migraine** | migraine headache, migraine with aura, migraine without aura |

### Hypertension subtypes

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **renovascular hypertension** | renovascular disease |
| 2 | **essential hypertension** | primary hypertension |

### Urological

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **overactive bladder** | urge incontinence, urge urinary incontinence, urgency incontinence |

### Neonatal

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **rh hemolytic disease** | hemolytic disease of the newborn, rh incompatibility, rh isoimmunization |
| 2 | **neonatal sepsis** | sepsis, septicemia |

### Thyroid

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **hyperthyroidism** | neonatal thyrotoxicosis, thyrotoxicosis |
| 2 | **hypothyroidism** | congenital hypothyroidism, transient hypothyroidism |

### Oncology / Hematology (extended)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **waldenstrom macroglobulinemia** | waldenstroms macroglobulinemia |

### Other

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **end stage renal disease** | esrd |
| 2 | **acute tubular necrosis** | atn |
| 3 | **hypertension** | high blood pressure, htn |
| 4 | **hypotension** | low blood pressure |
| 5 | **drug-induced nephropathy** | drug-induced interstitial nephritis, drug-induced nephrotoxicity, medication-induced nephrotoxicity |
| 6 | **peripheral artery disease** | pad, peripheral arterial disease, peripheral vascular disease, pvd |
| 7 | **critical limb ischemia** | chronic limb-threatening ischemia, cli |

### Neonatal / Blood group

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **rh or abo incompatibility** | abo incompatibility, blood group incompatibility, rh incompatibility, rh isoimmunization |

### Vascular / Erectile

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **vascular insufficiency** | arterial insufficiency, arteriosclerosis, atherosclerosis, pad, peripheral arterial disease, peripheral artery disease |
| 2 | **neurogenic erectile dysfunction** | autonomic neuropathy, diabetic neuropathy, neuropathic erectile dysfunction |
| 3 | **drug induced erectile dysfunction** | erectile dysfunction due to medication, iatrogenic erectile dysfunction, medication induced erectile dysfunction |

### Epidural / Obstetric

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **epidural induced hypotension** | epidural anesthesia induced hypotension, epidural hypotension, neuraxial hypotension, spinal hypotension, sympathetic block, sympathetic blockade |
| 2 | **amniotic fluid embolism** | afe, anaphylactoid syndrome of pregnancy |

### Neuromuscular

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **congenital myasthenia gravis** | cms, congenital myasthenic syndrome, congenital myasthenic syndromes |

### Overdose / Intoxication

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **overdose** | drug intoxication, drug overdose, medication overdose, opioid overdose, substance intoxication, substance overdose |

### Infectious (categorical)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **various infectious diseases** | chikungunya, dengue fever, infectious disease, malaria, tropical infection, typhoid fever |
| 2 | **clostridium difficile** | c diff, c difficile, clostridioides difficile, clostridioides difficile infection, clostridium difficile infection |
| 3 | **streptococcal pharyngitis** | gas pharyngitis, group a strep, group a streptococcus, strep throat, streptococcus pyogenes pharyngitis |
| 4 | **infectious mononucleosis** | ebv, ebv infection, epstein barr virus, glandular fever, mono, mononucleosis |
| 5 | **cytomegalovirus** | cmv, cmv infection, cytomegalovirus infection |

### Toxicology / Poisoning

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **scombroid poisoning** | histamine fish poisoning, scombroid fish poisoning, scombroid toxicity |
| 2 | **ciguatera poisoning** | ciguatera, ciguatera fish poisoning, ciguatera toxicity |

### Surgical / Post-operative

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **wound infection** | incisional infection, postoperative infection, postoperative wound infection, ssi, surgical site infection, surgical wound infection |

### Reproductive / Gynecological

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **mullerian agenesis** | mayer rokitansky kuster hauser syndrome, mrkh, mrkh syndrome, mullerian aplasia, rokitansky syndrome, vaginal agenesis |
| 2 | **genitopelvic pain disorder** | dyspareunia, genito pelvic pain penetration disorder, vaginismus |

### Round 4 additions (cases 300-399 zero-recall analysis)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **pleuritis** | pleurisy |
| 2 | **bronchogenic cancer** | bronchial carcinoma, bronchogenic carcinoma, lung cancer |
| 3 | **tracheaectasy** | bronchiectasis, tracheal ectasia, tracheobronchiectasis |
| 4 | **anemia of chronic disease** | anemia of inflammation, chronic disease anemia, chronic inflammatory anemia |
| 5 | **dysthymia** | dysthymic disorder, persistent depressive disorder |
| 6 | **angina pectoris** | angina, stable angina |
| 7 | **foreign body aspiration** | airway foreign body, foreign body in airway, foreign body in bronchus, foreign body in trachea, tracheal foreign body |
| 8 | **poststreptococcal glomerulonephritis** | acute poststreptococcal glomerulonephritis, apsgn, post streptococcal glomerulonephritis, psgn |
| 9 | **wilms tumor** | nephroblastoma, wilm tumor |
| 10 | **lymphangiosarcoma** | stewart treves syndrome |
| 11 | **attention deficit hyperactivity disorder** | add, adhd, attention deficit disorder |
| 12 | **cerebral infarction** | cerebral ischemia, ischemic stroke |
| 13 | **gastrointestinal infection** | gastroenteritis, gi infection, infectious gastroenteritis |
| 14 | **inflammatory bowel syndrome** | ibd, inflammatory bowel disease |
| 15 | **pulmonary infarction** | pulmonary thromboembolism |
| 16 | **breast abscess** | lactational mastitis, mastitis, periareolar abscess |

### Round 4b — remaining zero-recall fixes

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **kidney stones** | nephrolithiasis, renal calculi, renal stones, urolithiasis |
| 2 | **infectious endocarditis** | bacterial endocarditis, infective endocarditis |
| 3 | **lewy body dementia** | dementia with lewy bodies, dlb, lewy body disease |
| 4 | **major depressive disorder** | clinical depression, depression, mdd, severe depression, unipolar depression |
| 5 | **alcoholic liver disease** | alcohol induced liver disease, alcohol liver disease, alcohol related liver disease |
| 6 | **syphilis** | treponema pallidum, treponema pallidum infection |
| 7 | **gonorrhea** | gonococcal infection, neisseria gonorrhoeae |
| 8 | **nightmares** | nightmare disorder |
| 9 | **night terrors** | sleep terror disorder, sleep terrors |
| 10 | **medial collateral ligament injury** | mcl injury, mcl sprain, mcl tear, medial collateral ligament sprain, medial collateral ligament tear |
| 11 | **anterior cruciate ligament injury** | acl injury, acl rupture, acl tear, anterior cruciate ligament rupture, anterior cruciate ligament tear |
| 12 | **lateral collateral ligament injury** | lateral collateral ligament sprain, lateral collateral ligament tear, lcl injury, lcl sprain, lcl tear |
| 13 | **posterior cruciate ligament injury** | pcl injury, pcl rupture, pcl tear, posterior cruciate ligament rupture, posterior cruciate ligament tear |
| 14 | **acute arterial occlusion** | acute arterial embolism, acute limb ischemia, arterial embolism, arterial occlusion |
| 15 | **nutritional deficiency anemia** | nutritional deficiencies, nutritional deficiency |

### Vestibular / ENT

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **vestibular neuronitis** | acute vestibular neuritis, acute vestibular neuronitis, acute vestibular syndrome, vestibular neuritis |
| 2 | **labyrinthitis** | acute labyrinthitis, vestibular labyrinthitis |
| 3 | **benign positional vertigo** | benign paroxysmal positional vertigo, bppv, positional vertigo |

### GI / Abdominal

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **intestinal tuberculosis** | abdominal tuberculosis, gastrointestinal tuberculosis, tuberculosis of intestine, tuberculous enteritis |
| 2 | **intestinal obstruction** | bowel obstruction, ileus, large bowel obstruction, mechanical bowel obstruction, small bowel obstruction |
| 3 | **congenital megacolon** | aganglionic megacolon, hirschsprung disease, hirschsprungs disease |
| 4 | **duodenal bulbar ulcer** | duodenal erosion, duodenal ulcer, peptic ulcer disease |
| 5 | **bleeding peptic ulcer** | gastric ulcer with bleeding, peptic ulcer disease, peptic ulcer hemorrhage, upper gi bleeding |
| 6 | **esophagitis** | eosinophilic esophagitis, erosive esophagitis, pill esophagitis, reflux esophagitis |
| 7 | **liver cirrhosis** | alcoholic cirrhosis, cirrhosis, cirrhosis of liver, hepatic cirrhosis |
| 8 | **liver abscess** | amoebic liver abscess, hepatic abscess, pyogenic liver abscess |
| 9 | **ulcerative colitis** | inflammatory bowel disease, uc |
| 10 | **irritable bowel disease (constipation type)** | constipation predominant ibs, ibs, ibs c, irritable bowel disease, irritable bowel syndrome |

### Pulmonary

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **emphysema** | chronic obstructive pulmonary disease, copd, pulmonary emphysema |
| 2 | **lung abscess** | lung infection with cavitation, pulmonary abscess |
| 3 | **bronchial asthma** | asthma, bronchospasm, reactive airway disease |
| 4 | **lung cancer** | bronchogenic cancer, bronchogenic carcinoma, non small cell lung cancer, pulmonary malignancy, pulmonary neoplasm, small cell lung cancer |

### Neurology / Spine

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **disk herniation** | disc herniation, herniated disc, herniated disk, intervertebral disc herniation, prolapsed disc, slipped disc |
| 2 | **intervertebral disk hernia** | disc herniation, disk herniation, herniated disc, herniated disk, intervertebral disc herniation |
| 3 | **intracranial neoplasm** | brain neoplasm, brain tumor, brain tumour, cerebral neoplasm, cns tumor, intracranial tumor |
| 4 | **carotid sinus syndrome** | carotid sinus hypersensitivity, carotid sinus syncope |
| 5 | **neurologic syncope** | neurocardiogenic syncope, neurological syncope, reflex syncope, vasovagal syncope |

### Psychiatric

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **posttraumatic stress disorder** | post traumatic stress disorder, post-traumatic stress disorder, ptsd |
| 2 | **schizoaffective disorder** | schizoaffective, schizophrenia with mood disorder |

### Urinary

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **stress incontinence** | stress urinary incontinence, sui, urinary stress incontinence |
| 2 | **mixed incontinence** | mixed urinary incontinence, mui |
| 3 | **overactive bladder** | urge incontinence, urge urinary incontinence, urgency incontinence |

### Endocrine / Metabolic

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **hypocalcemia** | calcium deficiency, hypocalcaemia, low calcium |
| 2 | **simple obesity** | metabolic syndrome, morbid obesity, obesity |

### Tuberculosis variants

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **tuberculosis of lumbar vertebrae** | pott disease, potts disease, skeletal tuberculosis, spinal tuberculosis, tuberculous spondylitis, vertebral tuberculosis |

### Fracture matching

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **fracture** | bone fracture, skeletal fracture |

### Infection categorical

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **infection (cellulitis or osteomyelitis)** | bone infection, cellulitis, osteomyelitis, skin infection, soft tissue infection |

### Hepatitis

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **alcoholic hepatitis** | alcohol induced hepatitis, alcoholic liver disease |
| 2 | **drug-induced hepatitis** | dili, drug induced liver injury, medication induced hepatitis, toxic hepatitis |

### Obesity subtypes (GT uses these)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **gonadal obesity** | endocrine obesity, obesity |
| 2 | **hypothalamic obesity** | endocrine obesity, obesity |
| 3 | **cortisol obesity** | cushing syndrome, cushings syndrome, obesity |
| 4 | **pancreatic obesity** | metabolic syndrome, obesity |

### Vague/categorical GT labels

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **an overdose of a substance** | acute intoxication, drug overdose, mixed drug intoxication, opioid overdose, overdose, substance overdose |
| 2 | **a psychiatric episode** | mental health crisis, psychiatric decompensation, psychiatric emergency, psychotic episode |
| 3 | **a metabolic issue** | electrolyte imbalance, metabolic acidosis, metabolic alkalosis, metabolic derangement, metabolic disorder |
| 4 | **pneumonia (bacterial or viral)** | bacterial pneumonia, cap, community acquired pneumonia, pneumonia, viral pneumonia |
| 5 | **infections from bacteria or viruses** | bacterial infection, infected bite, infectious disease, infectious wound, viral infection |
| 6 | **bites or stings from insects or animals** | bite or sting, brown recluse spider bite, infected bite or sting, insect bite, snake bite, spider bite, venomous snake bite |
| 7 | **allergic or toxic reaction to plants or substances** | allergic contact dermatitis, allergic reaction, anaphylaxis, contact dermatitis, toxic reaction |
| 8 | **bladder or kidney injury** | bladder injury, bladder trauma, kidney injury, renal injury, renal trauma |
| 9 | **bladder or kidney cancer** | bladder cancer, kidney cancer, renal cell carcinoma, transitional cell carcinoma, urothelial carcinoma |
| 10 | **side effects of chemotherapy** | chemotherapy induced, chemotherapy induced hematuria, chemotherapy side effects, chemotherapy toxicity, drug toxicity |
| 11 | **renal or bladder tumors** | bladder cancer, kidney cancer, renal cell carcinoma, urothelial carcinoma |
| 12 | **systemic infection** | bacteremia, sepsis, septicemia, systemic inflammatory response |
| 13 | **infection from bacteria or viruses** | bacterial infection, infectious disease, viral infection |

### Pathogen-as-diagnosis (GT lists organisms)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **staphylococcus aureus** | mrsa, mssa, osteomyelitis, septic arthritis, staph infection, staphylococcal infection |
| 2 | **streptococcus pyogenes** | cellulitis, group a strep, necrotizing fasciitis, strep infection, streptococcal infection |
| 3 | **haemophilus influenzae** | h influenzae infection, haemophilus infection |
| 4 | **salmonella species** | salmonella, salmonella infection, salmonellosis |
| 5 | **kingella kingae** | kingella infection, kingella osteomyelitis |
| 6 | **streptococcus pneumoniae infection** | pneumococcal infection, pneumococcal meningitis, pneumococcal pneumonia, streptococcus pneumoniae |
| 7 | **haemophilus influenzae infection** | h influenzae, haemophilus infection, haemophilus influenzae |
| 8 | **salmonella infection** | enteric fever, salmonella, salmonella species, salmonellosis |

### Hepatitis B

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **hepatitis b vaccination** | completed hbv vaccination, hbv vaccination, hepatitis b immune status, hepatitis b immunity |

### Vague categorical GT labels

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **various infectious diseases** | chikungunya, dengue fever, infectious disease, malaria, tropical infection, typhoid fever |
| 2 | **fungal infections** | aspergillosis, blastomycosis, coccidioidomycosis, fungal infection, histoplasmosis, paracoccidioidomycosis |
| 3 | **liver parasites like echinococcus and fasciola** | cystic echinococcosis, echinococcosis, fasciola hepatica, fascioliasis, hepatic hydatid cyst, hepatic hydatidosis, hydatid cyst |
| 4 | **diseases of the vestibular apparatus** | acute vestibular syndrome, benign paroxysmal positional vertigo, bppv, labyrinthitis, meniere disease, vestibular disorder, vestibular neuritis, vestibular neuronitis |
| 5 | **ophthalmologic diseases** | eye disease, nystagmus, ophthalmologic disease, optic neuritis, visual disturbance |
| 6 | **sepsis from a different source** | bloodstream infection, catheter related bloodstream infection, central line associated bloodstream infection, clabsi, sepsis, septicemia |
| 7 | **sexually transmitted infection (gonorrhea, chlamydia, syphilis)** | chlamydia, chlamydial infection, gonococcal infection, gonorrhea, sexually transmitted infection, std, sti, syphilis |

### Polyps

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **hyperplastic polyp** | colon polyp, colonic polyp, colorectal polyp |
| 2 | **tubular adenoma** | adenomatous polyp, colon adenoma, colorectal adenoma |
| 3 | **tubulovillous adenoma** | adenomatous polyp, colon adenoma, colorectal adenoma |
| 4 | **villous adenoma** | adenomatous polyp, colon adenoma, colorectal adenoma |

### Cardiac / Ischemia

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **myocardial ischemia** | acute coronary syndrome, angina, angina pectoris, cardiac ischemia, coronary artery disease |
| 2 | **cocaine-induced myocardial ischemia** | acute coronary syndrome, cocaine cardiomyopathy, cocaine induced chest pain |
| 3 | **cardiogenic syncope** | cardiac arrhythmia, cardiac conduction disorder, cardiac conduction system disorder, cardiac syncope |

### Seizures

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **focal seizures** | focal epilepsy, partial seizures, seizure disorder, temporal lobe epilepsy |
| 2 | **generalized seizures** | epilepsy, generalized tonic clonic seizure, grand mal seizure, seizure disorder, tonic clonic seizures |
| 3 | **convulsive movement in hysteria** | conversion disorder, functional seizures, pnes, psychogenic non epileptic seizures |

### Pediatric / Congenital

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **cretinism** | congenital hypothyroidism, neonatal hypothyroidism |
| 2 | **rickets** | nutritional rickets, vitamin d deficiency |
| 3 | **hydrocephaly** | congenital hydrocephalus, hydrocephalus |
| 4 | **physiologic jaundice** | neonatal jaundice, newborn jaundice, physiological jaundice |
| 5 | **abo incompatibility** | abo hemolytic disease, abo hemolytic disease of newborn, abo isoimmunization |

### Neck / Lymph

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **cervical lymphadenitis** | cervical lymphadenopathy, lymphadenopathy, neck lymphadenopathy |
| 2 | **tuberculous lymphadenitis** | lymph node tuberculosis, lymphadenopathy, scrofula |
| 3 | **malignant lymphoma** | hodgkin lymphoma, lymphoma, non hodgkin lymphoma |
| 4 | **thyroid adenoma** | thyroid mass, thyroid nodule |
| 5 | **thyroid carcinoma** | follicular thyroid cancer, papillary thyroid cancer, thyroid cancer |
| 6 | **nonspecific lymphadenitis** | bacterial lymphadenitis, lymphadenitis, lymphadenopathy, reactive lymphadenopathy |

### Musculoskeletal

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **humeral fracture** | fracture of the humerus, humerus fracture, proximal humerus fracture |
| 2 | **nedc muscle strain** | cervical muscle strain, cervical strain, muscle strain, neck muscle strain |
| 3 | **spinal disk herniation** | cervical herniated disc, disc herniation, disk herniation, herniated disc, lumbar disc herniation |
| 4 | **myofascitis of lower back** | back strain, lower back pain, lumbar myofascial pain, muscle strain, myofascial pain |
| 5 | **acute back sprain** | back strain, lumbar sprain, muscle strain, musculoskeletal back pain |
| 6 | **lumbar flexion compression fractures** | compression fracture, lumbar compression fracture, vertebral compression fracture |
| 7 | **tennis elbow (lateral epicondylitis)** | lateral epicondylalgia, lateral epicondylitis, tennis elbow |

### Hearing

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **prasbycusis** | age related hearing loss, presbycusis, sensorineural hearing loss |
| 2 | **cochlear nerve damage** | auditory neuropathy, cochlear damage, sensorineural hearing loss |
| 3 | **otosderosis** | conductive hearing loss, otosclerosis |

### Psychiatric (additional)

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **social phobia** | social anxiety, social anxiety disorder |
| 2 | **agoraphobia/specific phobia** | agoraphobia, phobic disorder, specific phobia |
| 3 | **panic attack** | acute panic, anxiety attack, panic disorder |

### Prostate

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **benign prostatic hypertrophy (bph)** | benign prostatic hyperplasia, bph, prostatic hyperplasia, prostatic hypertrophy |

### GI specifics

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **pyloric obstruction** | gastric outlet obstruction, pyloric stenosis |
| 2 | **gastric perforation** | gastrointestinal perforation, peptic ulcer perforation, perforated ulcer |
| 3 | **functional dyspepsia** | dyspepsia, indigestion, non ulcer dyspepsia |
| 4 | **redundant sigmoid colon** | dolichosigmoid, elongated sigmoid, sigmoid volvulus |
| 5 | **intestinal adhesion** | abdominal adhesions, adhesive bowel obstruction, postoperative adhesions |

### Misc

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **analgesic nephropathy** | analgesic induced nephropathy, analgesic induced papillary necrosis, nsaid nephropathy |
| 2 | **consolidation** | bacterial pneumonia, community acquired pneumonia, lung consolidation, pneumonia, pulmonary consolidation |
| 3 | **pleural effusion** | exudative effusion, fluid in pleural space, hydrothorax |
| 4 | **nasopharyngeal carcinoma with neck metastasis** | head and neck cancer, nasopharyngeal cancer, nasopharyngeal carcinoma, squamous cell carcinoma |
| 5 | **fistula of the second or third branchial cleft** | branchial anomaly, branchial cleft cyst, branchial cleft fistula, lateral neck cyst |

### Round 5c — final zero-recall fixes

| # | Canonical Term (Ground Truth) | Accepted Aliases |
|--:|---|---|
| 1 | **bacterial food poisoning** | bacterial gastroenteritis, food poisoning, foodborne illness, gastroenteritis |
| 2 | **tumor of the colon** | colon cancer, colon tumor, colonic neoplasm, colorectal cancer |
| 3 | **polyp of colon** | adenomatous polyp, colon polyp, colonic polyp, colorectal polyp |
| 4 | **tumor of small intestine** | gastric cancer, small bowel neoplasm, small bowel tumor, small intestine cancer |
| 5 | **achalasia of cardia** | achalasia, cardiospasm, esophageal achalasia |
| 6 | **esophageal hiatal hernia** | diaphragmatic hernia, hiatal hernia, hiatus hernia |
| 7 | **bulbar paralysis** | bulbar palsy, lower motor neuron lesion, pseudobulbar palsy |
| 8 | **prostatic hyperplasia** | benign prostatic hyperplasia, benign prostatic hypertrophy, bph, prostatic hypertrophy |
| 9 | **kidney stone** | kidney stones, nephrolithiasis, renal calculi, renal stones, urolithiasis |
| 10 | **physiological vertigo** | benign positional vertigo, motion sickness, positional vertigo, vertigo |
| 11 | **rib fracture** | chest wall fracture, costal fracture, costochondritis, fractured rib |

## Part 2: Clinical Hierarchies (Supertype / Subtype)

A pipeline diagnosis matching a **subtype** counts as a partial match
for the **supertype** ground truth, and vice versa.

### General

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **myocardial infarction** | acute mi, non-st elevation myocardial infarction, nstemi, st elevation myocardial infarction, stemi |
| 2 | **pneumonia** | aspiration pneumonia, bacterial pneumonia, coccidioidomycosis, community-acquired pneumonia, fungal pneumonia, histoplasmosis, hospital-acquired pneumonia, pneumocystis jirovecii pneumonia, pneumocystis pneumonia, ventilator-associated pneumonia, viral pneumonia |
| 3 | **arthritis** | gouty arthritis, osteoarthritis, psoriatic arthritis, reactive arthritis, rheumatoid arthritis, septic arthritis |
| 4 | **acute kidney injury** | contrast-induced nephropathy, drug-induced aki, intrinsic aki, ischemic aki, nephrotoxic aki, postrenal aki, prerenal aki |
| 5 | **heart failure** | acute heart failure, chronic heart failure, congestive heart failure, diastolic heart failure, systolic heart failure |
| 6 | **diabetes mellitus** | drug-induced diabetes, gestational diabetes, secondary diabetes, type 1 diabetes, type 2 diabetes |
| 7 | **vasculitis** | anca-associated vasculitis, drug-induced vasculitis, hypersensitivity vasculitis, necrotizing vasculitis, systemic vasculitis |
| 8 | **nephropathy** | contrast-induced nephropathy, diabetic nephropathy, drug-induced nephropathy, hypertensive nephropathy, ischemic nephropathy |
| 9 | **aspergillosis** | abpa, acute pulmonary aspergillosis, allergic aspergillosis, allergic bronchopulmonary aspergillosis, aspergillus pneumonia, invasive aspergillosis |
| 10 | **fungal pneumonia** | aspergillosis, blastomycosis, coccidioidomycosis, cryptococcosis, histoplasmosis, pneumocystis pneumonia |
| 11 | **hemolytic anemia** | autoimmune hemolytic anemia, glucose-6-phosphate dehydrogenase deficiency, hereditary spherocytosis, microangiopathic hemolytic anemia, paroxysmal nocturnal hemoglobinuria, sickle cell anemia |
| 12 | **thrombotic microangiopathy** | atypical hemolytic uremic syndrome, complement-mediated ttp, hemolytic uremic syndrome, thrombotic thrombocytopenic purpura |
| 13 | **bleeding disorders** | disseminated intravascular coagulation, hemophilia, heparin induced thrombocytopenia, immune thrombocytopenic purpura, thrombocytopenia, von willebrand disease |
| 14 | **anemia** | aplastic anemia, chronic disease anemia, hemolytic anemia, iron deficiency anemia, megaloblastic anemia, sickle cell anemia |
| 15 | **gastroenteritis** | bacterial gastroenteritis, infectious gastroenteritis, parasitic gastroenteritis, viral gastroenteritis |
| 16 | **neonatal bowel obstruction** | duodenal atresia, gastrointestinal obstruction, hirschsprung disease, intestinal atresia, malrotation, malrotation with midgut volvulus, meconium ileus, meconium plug syndrome, meconium-ileal atresia |
| 17 | **colorectal adenoma** | adenomatous polyp, tubular adenoma, tubulovillous adenoma, villous adenoma |
| 18 | **bacterial enteritis** | campylobacter, campylobacter enteritis, e coli, salmonella, salmonella enteritis, shigella |
| 19 | **antidepressants** | antidepressant overdose, maoi, selective serotonin reuptake inhibitor, snri, ssri, ssri overdose, tca, tricyclic antidepressant overdose, tricyclic antidepressants |
| 20 | **peripheral artery disease** | claudication, critical limb ischemia, femoral artery occlusion, iliac artery stenosis |
| 21 | **parkinsonism** | drug-induced parkinsonism, neuroleptic-induced parkinsonism, pseudoparkinsonism |
| 22 | **extrapyramidal side effects** | acute dystonic reaction, akathisia, dystonia, neuroleptic-induced parkinsonism, pseudoparkinsonism, tardive dyskinesia |
| 23 | **hypertension** | essential hypertension, malignant hypertension, medication-induced hypertension, primary hypertension, renovascular hypertension, secondary hypertension |
| 24 | **thyroid disease** | congenital hypothyroidism, goiter, hyperthyroidism, hypothyroidism, neonatal thyrotoxicosis, thyroid storm, thyrotoxicosis, transient hypothyroidism |

### Neuromuscular

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **myopathy** | becker muscular dystrophy, congenital myopathy, dermatomyositis, duchenne muscular dystrophy, inflammatory myopathy, limb girdle muscular dystrophy, muscular dystrophy, myositis, myotonic dystrophy, polymyositis |
| 2 | **anterior horn cell disease** | amyotrophic lateral sclerosis, poliomyelitis, progressive muscular atrophy, spinal muscular atrophy, spinal muscular atrophy type 1, spinal muscular atrophy type 2 |

### Peripheral neuropathy

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **peripheral neuropathy** | alcoholic neuropathy, autonomic neuropathy, chemotherapy induced neuropathy, diabetic neuropathy, motor neuropathy, sensory neuropathy |

### Infectious diseases (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **infectious diseases** | chikungunya, cholera, dengue, dengue fever, encephalitis, hepatitis a, hepatitis b, hepatitis c, hiv, leptospirosis, malaria, meningitis, sepsis, tuberculosis, typhoid, typhoid fever, yellow fever, zika |

### Overdose / Substance

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **overdose** | alcohol poisoning, drug intoxication, drug overdose, intoxication, medication overdose, opioid overdose, substance intoxication, substance overdose |

### Psychiatric (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **psychiatric episode** | mental health crisis, psychiatric decompensation, psychiatric emergency, psychosis, psychotic episode, suicide attempt |

### Metabolic (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **metabolic disorder** | acid base disorder, electrolyte imbalance, metabolic acidosis, metabolic alkalosis, metabolic issue |

### Traumatic injury (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **traumatic injury** | blunt trauma, head injury, neurological trauma, physical trauma, trauma, traumatic brain injury |

### Erectile dysfunction subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **erectile dysfunction** | drug induced erectile dysfunction, hormonal erectile dysfunction, neurogenic erectile dysfunction, psychogenic erectile dysfunction, vascular erectile dysfunction |

### Hematologic malignancy categories

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **leukemias** | acute lymphoblastic leukemia, acute myeloid leukemia, chronic lymphocytic leukemia, chronic myeloid leukemia, hairy cell leukemia, leukemia |
| 2 | **lymphomas** | burkitt lymphoma, chronic lymphocytic leukemia, diffuse large b cell lymphoma, follicular lymphoma, hodgkin lymphoma, lymphoma, mantle cell lymphoma, non hodgkin lymphoma |
| 3 | **myeloproliferative disorders** | chronic myeloid leukemia, essential thrombocythemia, myelofibrosis, myeloproliferative neoplasm, polycythemia vera |

### Reactive / Inflammatory (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **immune response to an inflammatory condition** | inflammatory response, leukocytosis, reactive leukocytosis, reactive lymphocytosis, secondary leukocytosis |

### Illicit drug use (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **illicit drug use** | amphetamine intoxication, cannabis intoxication, cocaine intoxication, drug intoxication, methamphetamine intoxication, opioid intoxication, stimulant intoxication, synthetic cannabinoid intoxication |

### Sleep disorders

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **circadian rhythm sleep disorder** | advanced sleep phase syndrome, circadian rhythm disorder, delayed sleep phase syndrome, irregular sleep wake rhythm disorder, jet lag disorder, non 24 hour sleep wake disorder, shift work sleep disorder |

### Endocarditis / pathogen-to-disease

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **infective endocarditis** | bacterial endocarditis, staphylococcus aureus endocarditis, streptococcus sanguinis, streptococcus viridans, subacute bacterial endocarditis |

### Antipsychotic side effects (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **side effects from antipsychotic medications** | akathisia, antipsychotic side effects, drug induced parkinsonism, dystonia, extrapyramidal side effects, extrapyramidal symptoms, medication induced movement disorder, neuroleptic malignant syndrome, pseudoparkinsonism, tardive dyskinesia |
| 2 | **dopamine antagonist** | drug induced parkinsonism, extrapyramidal symptoms, medication induced movement disorder, neuroleptic malignant syndrome, tardive dyskinesia |

### Stroke subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **stroke** | cryptogenic stroke, embolic stroke, hemorrhagic stroke, ischemic stroke, lacunar stroke, thrombotic stroke |
| 2 | **cerebrovascular accident** | cryptogenic stroke, embolic stroke, hemorrhagic stroke, ischemic stroke, lacunar stroke, thrombotic stroke |

### Food poisoning (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **food poisoning** | botulism, campylobacter, ciguatera fish poisoning, ciguatera poisoning, salmonella, scombroid fish poisoning, scombroid poisoning, shellfish poisoning |

### Allergic reaction subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **allergic reaction** | anaphylactic reaction, anaphylactic shock, anaphylaxis, drug allergy, food allergy, shellfish allergy |

### Medication side effects (categorical)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **medication side effects** | adverse drug reaction, antibiotic associated diarrhea, anticholinergic poisoning, anticholinergic syndrome, anticholinergic toxicity, drug reaction, drug side effect, drug side effects, medication side effect |

### Intra-abdominal infection subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **intra abdominal infection** | abdominal abscess, intra abdominal abscess, pelvic abscess, peritonitis, subphrenic abscess |

### Pelvic floor / Gynecological

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **pelvic floor dysfunction** | levator ani syndrome, pelvic floor myalgia, vaginismus, vestibulodynia, vulvodynia |
| 2 | **vulvodynia** | generalized vulvodynia, provoked vestibulodynia, vestibulodynia |

### Round 4 additions (cases 300-399)

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **acute coronary syndrome** | myocardial infarction, non st elevation myocardial infarction, nstemi, st elevation myocardial infarction, stemi, unstable angina |
| 2 | **pulmonary embolism** | pulmonary infarction, pulmonary thromboembolism |
| 3 | **congestive heart failure** | cardiogenic pulmonary edema, diastolic heart failure, left heart failure, left sided heart failure, pulmonary edema, right heart failure, right sided heart failure, systolic heart failure |
| 4 | **lung cancer** | adenocarcinoma of lung, bronchial carcinoma, bronchogenic cancer, bronchogenic carcinoma, non small cell lung cancer, small cell lung cancer, squamous cell carcinoma of lung |
| 5 | **asthma** | acute asthma, acute asthma attack, acute bronchospasm, allergic asthma, asthma exacerbation, bronchial asthma, exercise induced asthma, status asthmaticus |
| 6 | **bronchitis** | acute bronchitis, chronic bronchitis |
| 7 | **skull fracture** | basilar skull fracture, depressed skull fracture, temporal bone fracture |
| 8 | **intracranial hemorrhage** | cerebral hemorrhage, epidural hematoma, intracerebral hemorrhage, subarachnoid hemorrhage, subdural hematoma |
| 9 | **intracranial infection** | brain abscess, cerebral abscess, encephalitis, meningitis |
| 10 | **renal disease** | acute kidney injury, chronic kidney disease, glomerulonephritis, nephritis, nephrotic syndrome, renal failure |
| 11 | **electrolyte abnormalities** | electrolyte imbalance, hypercalcemia, hyperkalemia, hypernatremia, hypocalcemia, hypokalemia, hypomagnesemia, hyponatremia, magnesium deficiency |
| 12 | **nutritional deficiencies** | folate deficiency, iron deficiency, iron deficiency anemia, nutritional deficiency anemia, pernicious anemia, thiamine deficiency, vitamin b12 deficiency, vitamin deficiency |
| 13 | **glomerulonephritis** | acute poststreptococcal glomerulonephritis, iga nephropathy, lupus nephritis, membranoproliferative glomerulonephritis, membranous nephropathy, poststreptococcal glomerulonephritis, rapidly progressive glomerulonephritis |
| 14 | **hyperthyroidism** | graves disease, thyroid storm, thyrotoxicosis, toxic adenoma, toxic multinodular goiter |
| 15 | **megaloblastic anemia** | b12 deficiency anemia, folate deficiency anemia, pernicious anemia, vitamin b12 deficiency |

### Vertigo / Vestibular

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **vertigo** | benign paroxysmal positional vertigo, bppv, central vertigo, labyrinthitis, meniere disease, positional vertigo, vestibular neuritis, vestibular neuronitis |

### Syncope

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **syncope** | cardiac syncope, carotid sinus syncope, neurocardiogenic syncope, neurologic syncope, orthostatic syncope, reflex syncope, vasovagal syncope |

### Tuberculosis subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **tuberculosis** | genitourinary tuberculosis, intestinal tuberculosis, miliary tuberculosis, pott disease, pulmonary tuberculosis, renal tuberculosis, skeletal tuberculosis, spinal tuberculosis, tuberculosis of lumbar vertebrae, tuberculous meningitis |

### Fracture subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **fracture** | ankle fracture, cervical fracture, clavicle fracture, compression fracture, femur fracture, hip fracture, humerus fracture, pathological fracture, radial fracture, radius fracture, rib fracture, skull fracture, stress fracture, tibia fracture, ulna fracture, vertebral fracture |

### Incontinence

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **urinary incontinence** | functional incontinence, mixed incontinence, mixed urinary incontinence, overflow incontinence, stress incontinence, stress urinary incontinence, urge incontinence |

### Hepatitis

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **hepatitis** | alcoholic hepatitis, autoimmune hepatitis, drug induced hepatitis, hepatitis a, hepatitis b, hepatitis c, hepatitis d, hepatitis e, toxic hepatitis, viral hepatitis |

### Obesity subtypes

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **obesity** | cortisol obesity, gonadal obesity, hypothalamic obesity, metabolic syndrome, morbid obesity, pancreatic obesity, simple obesity |

### Disc / Spine

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **spinal disc disease** | cervical herniated disc, degenerative disc disease, disc herniation, disk herniation, herniated disc, intervertebral disk hernia, lumbar disc herniation, spinal stenosis |

### Pyelonephritis

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **pyelonephritis** | acute nephropyelitis, acute pyelonephritis, chronic nephropyelitis, chronic pyelonephritis, kidney infection, upper urinary tract infection |

### Brain tumors

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **brain tumor** | astrocytoma, brain neoplasm, cerebral neoplasm, cns tumor, glioblastoma, glioma, intracranial neoplasm, intracranial tumor, medulloblastoma, meningioma |

### Esophageal disease

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **esophageal disease** | achalasia, barrett esophagus, esophageal cancer, esophageal hiatal hernia, esophageal motility disorder, esophageal spasm, esophageal stricture, esophagitis, gastroesophageal reflux disease |

### Colorectal neoplasms

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **colorectal neoplasm** | adenomatous polyp, colon cancer, colonic polyp, colorectal adenoma, colorectal cancer, polyp of colon, rectal cancer, tumor of the colon |

### Inflammatory bowel disease

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **inflammatory bowel disease** | colitis, crohn disease, crohns disease, inflammatory bowel syndrome, ulcerative colitis |

### Cyanosis

| # | Supertype | Subtypes |
|--:|---|---|
| 1 | **cyanosis** | central cyanosis, methemoglobinemia, mixed cyanosis, peripheral cyanosis, sulfhemoglobinemia |

## Part 3: Known Gaps — Needs Review

These mismatches were found in the Gemma 4 MoE 20-case evaluation (2026-04-06).
The pipeline produced clinically correct diagnoses that the evaluator
failed to match due to missing synonyms.

| Case | Ground Truth | Pipeline Output | Action Needed |
|---:|---|---|---|
| 458 | Diabetic peripheral neuropathy | Diabetic Polyneuropathy | Add synonym |
| 458 | Insulin-induced hypoglycemia | Hypoglycemic Episodes (Iatrogenic/Reactive) | Add synonym |
| 458 | Organic erectile dysfunction | Diabetic Autonomic Neuropathy | Review — related? |
| 29 | Exogenous insulin administration | Factitious Hypoglycemia (Exogenous Insulin Administration) | Add synonym |
| 29 | Factitious disorder | Factitious Hypoglycemia | Add synonym |
| 29 | Severe liver disease | — | Pipeline missed |
| 29 | Adrenal insufficiency | — | Pipeline missed |
| 48 | Inadvertent surgical removal of parathyroid glands | Hypoparathyroidism (Post-Surgical) | Add synonym |
| 48 | Hypomagnesemia | Hypomagnesemia-Induced Hypocalcemia | Add synonym |
| 48 | Hypocalcemia | Hypomagnesemia-Induced Hypocalcemia | Add synonym |
| 48 | Hypothyroidism | — | Pipeline missed |
| 512 | Diverticulitis | — | Pipeline missed |
| 512 | Peptic ulcer disease | — | Pipeline missed |
| 512 | Gastroenteritis | — | Pipeline missed |
| 512 | Acute pancreatitis | — | Pipeline missed |

---

**Total synonym groups:** 254  
**Total hierarchy groups:** 79  
**Last updated:** 2026-04-07  
**Source:** `benchmark/ddx_evaluator.py` → `ClinicalEquivalenceEngine`  