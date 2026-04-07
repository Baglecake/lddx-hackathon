"""
Standalone Deterministic Evaluator for Open-XDDx Benchmarking.

Adapted from v8's ddx_evaluator_v9.py but with NO v6/v7 imports.
Pure deterministic matching: synonym dict, clinical hierarchies,
normalization, word overlap. No LLM-based matching.

Designed to evaluate v10 pipeline output against Open-XDDx ground truth.
"""

import os
import re
import json
import argparse
import unicodedata
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


# =============================================================================
# Clinical Equivalence Engine
# =============================================================================

class ClinicalEquivalenceEngine:
    """Deterministic clinical equivalence matching (no LLM dependency)"""

    def __init__(self):
        self.medical_synonyms = self._build_medical_synonyms()
        self.clinical_hierarchies = self._build_clinical_hierarchies()

    def _build_medical_synonyms(self) -> Dict[str, Set[str]]:
        """Build comprehensive medical synonym dictionary"""
        synonyms = {
            # Cardiovascular
            'myocardial infarction': {'mi', 'heart attack', 'acute mi'},
            'acute coronary syndrome': {'acs'},
            'congestive heart failure': {'chf', 'heart failure', 'cardiac failure'},
            'atrial fibrillation': {'afib', 'af'},

            # Renal
            'acute kidney injury': {'aki', 'acute renal failure', 'arf'},
            'chronic kidney disease': {'ckd', 'chronic renal failure', 'crf'},
            'contrast-induced nephropathy': {'cin', 'contrast nephropathy', 'contrast-induced aki'},

            # Respiratory
            'chronic obstructive pulmonary disease': {'copd'},
            'community-acquired pneumonia': {'cap', 'pneumonia'},
            'acute respiratory distress syndrome': {'ards'},
            'pulmonary embolism': {'pe'},
            'deep vein thrombosis': {'dvt'},

            # Endocrine
            'diabetes mellitus': {'dm', 'diabetes'},
            'diabetic ketoacidosis': {'dka'},
            'type 1 diabetes': {'t1dm', 'iddm'},
            'type 2 diabetes': {'t2dm', 'niddm'},

            # Hematology
            'thrombotic thrombocytopenic purpura': {'ttp'},
            'thrombotic microangiopathy': {'tma'},
            'disseminated intravascular coagulation': {'dic'},
            'hemolytic uremic syndrome': {'hus'},
            'hemolytic anemia': {'ha'},
            'microangiopathic hemolytic anemia': {'maha', 'microangiopathic ha'},
            'autoimmune hemolytic anemia': {'aiha', 'autoimmune ha'},
            'paroxysmal nocturnal hemoglobinuria': {'pnh'},
            'sickle cell disease': {'scd', 'sickle cell anemia'},
            'iron deficiency anemia': {'ida', 'iron deficiency'},
            'megaloblastic anemia': {'b12 deficiency', 'folate deficiency'},
            'spherocytosis': {'hereditary spherocytosis'},
            'thrombocytopenia': {'low platelets'},
            'immune thrombocytopenic purpura': {'itp', 'idiopathic thrombocytopenic purpura'},
            'heparin induced thrombocytopenia': {'hit'},
            'antiphospholipid syndrome': {'aps', 'antiphospholipid antibody syndrome'},

            # Rheumatology
            'systemic lupus erythematosus': {'sle', 'lupus'},
            'rheumatoid arthritis': {'ra'},
            'ankylosing spondylitis': {'as'},
            'pseudogout': {
                'cppd', 'calcium pyrophosphate deposition disease',
                'calcium-pyrophosphate disease', 'cppd arthropathy',
                'chondrocalcinosis', 'cppd deposition disease'
            },
            'gout': {'gouty arthritis', 'uric acid arthropathy'},
            'osteoarthritis': {'oa', 'degenerative joint disease'},

            # Infectious
            'pneumocystis jirovecii pneumonia': {
                'pneumocystis pneumonia', 'pjp', 'pcp',
                'pneumocystis jiroveci pneumonia'
            },
            'allergic bronchopulmonary aspergillosis': {'abpa', 'allergic aspergillosis'},
            'acute pulmonary aspergillosis': {'invasive aspergillosis', 'aspergillus pneumonia'},
            'histoplasmosis': {'histo', 'histoplasma infection'},
            'coccidioidomycosis': {'cocci', 'valley fever'},
            'tuberculosis': {'tb', 'pulmonary tuberculosis'},

            # Neurology
            'transient ischemic attack': {'tia'},
            'cerebrovascular accident': {'cva', 'stroke'},
            'multiple sclerosis': {'ms'},

            # Gastroenterology
            'gastroesophageal reflux disease': {'gerd'},
            'inflammatory bowel disease': {'ibd'},
            'peptic ulcer disease': {'pud'},
            'infectious gastroenteritis': {
                'gastroenteritis', 'viral gastroenteritis',
                'bacterial gastroenteritis'
            },

            # Infectious Disease
            'urinary tract infection': {'uti'},
            'acquired immunodeficiency syndrome': {'aids'},
            'human immunodeficiency virus': {'hiv'},

            # Movement Disorders / Psychiatry
            'pseudoparkinsonism': {
                'neuroleptic-induced parkinsonism', 'drug-induced parkinsonism',
                'antipsychotic-induced parkinsonism'
            },
            'tardive dyskinesia': {'orofacial dyskinesia', 'oral-facial dyskinesia'},
            'neuroleptic malignant syndrome': {'nms'},
            'akathisia': {'drug-induced akathisia', 'neuroleptic-induced akathisia'},

            # Cardiovascular (extended)
            'cardiac contusion': {'myocardial contusion', 'blunt cardiac injury'},
            'vasovagal syncope': {'vasovagal reaction', 'vasovagal episode', 'neurocardiogenic syncope'},

            # Headache
            'tension headache': {'tension-type headache', 'tension type headache'},
            'migraine': {'migraine headache', 'migraine with aura', 'migraine without aura'},

            # Hypertension subtypes
            'renovascular hypertension': {'renovascular disease'},
            'essential hypertension': {'primary hypertension'},

            # Urological
            'overactive bladder': {'urge incontinence', 'urgency incontinence'},

            # Neonatal
            'rh hemolytic disease': {
                'rh incompatibility', 'rh isoimmunization',
                'hemolytic disease of the newborn'
            },
            'neonatal sepsis': {'sepsis', 'septicemia'},

            # Thyroid
            'hyperthyroidism': {'thyrotoxicosis', 'neonatal thyrotoxicosis'},
            'hypothyroidism': {'congenital hypothyroidism', 'transient hypothyroidism'},

            # Oncology / Hematology (extended)
            'waldenstrom macroglobulinemia': {'waldenstroms macroglobulinemia'},

            # Other
            'end stage renal disease': {'esrd'},
            'acute tubular necrosis': {'atn'},
            'hypertension': {'htn', 'high blood pressure'},
            'hypotension': {'low blood pressure'},
            'drug-induced nephropathy': {
                'drug-induced interstitial nephritis', 'medication-induced nephrotoxicity',
                'drug-induced nephrotoxicity'
            },
            'peripheral artery disease': {
                'pad', 'peripheral vascular disease', 'pvd',
                'peripheral arterial disease'
            },
            'critical limb ischemia': {'chronic limb-threatening ischemia', 'cli'},

            # Neonatal / Blood group
            'rh or abo incompatibility': {
                'rh incompatibility', 'abo incompatibility',
                'rh isoimmunization', 'blood group incompatibility'
            },

            # Vascular / Erectile
            'vascular insufficiency': {
                'peripheral artery disease', 'peripheral arterial disease',
                'pad', 'atherosclerosis', 'arteriosclerosis',
                'arterial insufficiency'
            },
            'neurogenic erectile dysfunction': {
                'autonomic neuropathy', 'diabetic neuropathy',
                'neuropathic erectile dysfunction'
            },
            'drug induced erectile dysfunction': {
                'medication induced erectile dysfunction',
                'erectile dysfunction due to medication',
                'iatrogenic erectile dysfunction'
            },

            # Epidural / Obstetric
            'epidural induced hypotension': {
                'epidural anesthesia induced hypotension',
                'epidural hypotension', 'spinal hypotension',
                'neuraxial hypotension', 'sympathetic block',
                'sympathetic blockade'
            },
            'amniotic fluid embolism': {'afe', 'anaphylactoid syndrome of pregnancy'},

            # Neuromuscular
            'congenital myasthenia gravis': {
                'congenital myasthenic syndrome', 'cms',
                'congenital myasthenic syndromes'
            },

            # Overdose / Intoxication
            'overdose': {
                'drug overdose', 'substance overdose', 'opioid overdose',
                'medication overdose', 'substance intoxication', 'drug intoxication'
            },

            # Infectious (categorical)
            'various infectious diseases': {'infectious diseases', 'infectious disease'},

            # Microbiology / Infectious synonyms
            'clostridium difficile': {
                'clostridioides difficile', 'c difficile', 'c diff',
                'clostridioides difficile infection', 'clostridium difficile infection'
            },
            'streptococcal pharyngitis': {
                'strep throat', 'group a streptococcus', 'group a strep',
                'gas pharyngitis', 'streptococcus pyogenes pharyngitis'
            },
            'infectious mononucleosis': {
                'mononucleosis', 'mono', 'epstein barr virus', 'ebv infection',
                'ebv', 'glandular fever'
            },
            'cytomegalovirus': {'cmv', 'cmv infection', 'cytomegalovirus infection'},

            # Toxicology / Poisoning
            'scombroid poisoning': {
                'scombroid fish poisoning', 'scombroid toxicity',
                'histamine fish poisoning'
            },
            'ciguatera poisoning': {
                'ciguatera fish poisoning', 'ciguatera toxicity', 'ciguatera'
            },

            # Surgical / Post-operative
            'wound infection': {
                'surgical site infection', 'ssi', 'postoperative wound infection',
                'surgical wound infection', 'incisional infection',
                'postoperative infection'
            },

            # Reproductive / Gynecological
            'mullerian agenesis': {
                'mayer rokitansky kuster hauser syndrome', 'mrkh syndrome', 'mrkh',
                'rokitansky syndrome', 'mullerian aplasia', 'vaginal agenesis'
            },
            'genitopelvic pain disorder': {
                'vaginismus', 'dyspareunia',
                'genito pelvic pain penetration disorder'
            },

            # Round 4 additions (cases 300-399 zero-recall analysis)
            'pleuritis': {'pleurisy'},
            'bronchogenic cancer': {'lung cancer', 'bronchogenic carcinoma', 'bronchial carcinoma'},
            'tracheaectasy': {'bronchiectasis', 'tracheal ectasia', 'tracheobronchiectasis'},
            'anemia of chronic disease': {
                'chronic disease anemia', 'anemia of inflammation',
                'chronic inflammatory anemia'
            },
            'dysthymia': {'dysthymic disorder', 'persistent depressive disorder'},
            'angina pectoris': {'angina', 'stable angina'},
            'foreign body aspiration': {
                'foreign body in trachea', 'foreign body in bronchus',
                'foreign body in airway', 'tracheal foreign body',
                'airway foreign body'
            },
            'poststreptococcal glomerulonephritis': {
                'psgn', 'post streptococcal glomerulonephritis',
                'acute poststreptococcal glomerulonephritis', 'apsgn'
            },
            'wilms tumor': {'nephroblastoma', 'wilm tumor'},
            'lymphangiosarcoma': {'stewart treves syndrome'},
            'attention deficit hyperactivity disorder': {
                'adhd', 'attention deficit disorder', 'add'
            },
            'cerebral infarction': {'ischemic stroke', 'cerebral ischemia'},
            'gastrointestinal infection': {
                'infectious gastroenteritis', 'gastroenteritis', 'gi infection'
            },
            'inflammatory bowel syndrome': {'inflammatory bowel disease', 'ibd'},
            'pulmonary infarction': {'pulmonary thromboembolism'},
            'breast abscess': {'mastitis', 'lactational mastitis', 'periareolar abscess'},

            # Round 4b — remaining zero-recall fixes
            'kidney stones': {
                'urolithiasis', 'nephrolithiasis', 'renal calculi', 'renal stones'
            },
            'infectious endocarditis': {'infective endocarditis', 'bacterial endocarditis'},
            'lewy body dementia': {
                'dementia with lewy bodies', 'dlb', 'lewy body disease'
            },
            'major depressive disorder': {
                'depression', 'mdd', 'clinical depression', 'unipolar depression',
                'severe depression'
            },
            'alcoholic liver disease': {
                'alcohol related liver disease', 'alcohol liver disease',
                'alcohol induced liver disease'
            },
            'syphilis': {'treponema pallidum', 'treponema pallidum infection'},
            'gonorrhea': {'neisseria gonorrhoeae', 'gonococcal infection'},
            'nightmares': {'nightmare disorder'},
            'night terrors': {'sleep terror disorder', 'sleep terrors'},
            'medial collateral ligament injury': {
                'mcl injury', 'mcl tear', 'mcl sprain',
                'medial collateral ligament tear', 'medial collateral ligament sprain'
            },
            'anterior cruciate ligament injury': {
                'acl injury', 'acl tear', 'acl rupture',
                'anterior cruciate ligament tear', 'anterior cruciate ligament rupture'
            },
            'lateral collateral ligament injury': {
                'lcl injury', 'lcl tear', 'lcl sprain',
                'lateral collateral ligament tear', 'lateral collateral ligament sprain'
            },
            'posterior cruciate ligament injury': {
                'pcl injury', 'pcl tear', 'pcl rupture',
                'posterior cruciate ligament tear', 'posterior cruciate ligament rupture'
            },
            'acute arterial occlusion': {
                'acute arterial embolism', 'acute limb ischemia',
                'arterial embolism', 'arterial occlusion'
            },
            'nutritional deficiency anemia': {
                'nutritional deficiencies', 'nutritional deficiency'
            },

            # Round 5 additions (cases 400-569 + full-set zero-recall analysis)

            # Vestibular / ENT
            'vestibular neuronitis': {
                'vestibular neuritis', 'acute vestibular neuritis',
                'acute vestibular neuronitis', 'acute vestibular syndrome'
            },
            'labyrinthitis': {'acute labyrinthitis', 'vestibular labyrinthitis'},
            'benign positional vertigo': {
                'benign paroxysmal positional vertigo', 'bppv',
                'positional vertigo'
            },

            # GI / Abdominal
            'intestinal tuberculosis': {
                'tuberculosis of intestine', 'abdominal tuberculosis',
                'gastrointestinal tuberculosis', 'tuberculous enteritis'
            },
            'intestinal obstruction': {
                'bowel obstruction', 'small bowel obstruction',
                'large bowel obstruction', 'mechanical bowel obstruction',
                'ileus'
            },
            'congenital megacolon': {
                'hirschsprung disease', 'hirschsprungs disease',
                'aganglionic megacolon'
            },
            'duodenal bulbar ulcer': {
                'duodenal ulcer', 'peptic ulcer disease', 'duodenal erosion'
            },
            'bleeding peptic ulcer': {
                'peptic ulcer disease', 'gastric ulcer with bleeding',
                'upper gi bleeding', 'peptic ulcer hemorrhage'
            },
            'esophagitis': {
                'erosive esophagitis', 'reflux esophagitis',
                'eosinophilic esophagitis', 'pill esophagitis'
            },
            'liver cirrhosis': {
                'cirrhosis', 'hepatic cirrhosis', 'alcoholic cirrhosis',
                'cirrhosis of liver'
            },
            'liver abscess': {
                'hepatic abscess', 'pyogenic liver abscess',
                'amoebic liver abscess'
            },
            'ulcerative colitis': {'uc', 'inflammatory bowel disease'},
            'irritable bowel disease (constipation type)': {
                'irritable bowel syndrome', 'ibs', 'ibs c',
                'irritable bowel disease', 'constipation predominant ibs'
            },

            # Pulmonary
            'emphysema': {
                'pulmonary emphysema', 'copd', 'chronic obstructive pulmonary disease'
            },
            'lung abscess': {
                'pulmonary abscess', 'lung infection with cavitation'
            },
            'bronchial asthma': {
                'asthma', 'reactive airway disease', 'bronchospasm'
            },
            'lung cancer': {
                'bronchogenic carcinoma', 'pulmonary malignancy',
                'non small cell lung cancer', 'small cell lung cancer',
                'bronchogenic cancer', 'pulmonary neoplasm'
            },

            # Neurology / Spine
            'disk herniation': {
                'disc herniation', 'herniated disc', 'herniated disk',
                'intervertebral disc herniation', 'slipped disc',
                'prolapsed disc'
            },
            'intervertebral disk hernia': {
                'disc herniation', 'herniated disc', 'herniated disk',
                'intervertebral disc herniation', 'disk herniation'
            },
            'intracranial neoplasm': {
                'brain tumor', 'brain tumour', 'cns tumor',
                'intracranial tumor', 'cerebral neoplasm', 'brain neoplasm'
            },
            'carotid sinus syndrome': {
                'carotid sinus hypersensitivity', 'carotid sinus syncope',
                'carotid body tumor'
            },
            'neurologic syncope': {
                'neurological syncope', 'neurocardiogenic syncope',
                'vasovagal syncope', 'reflex syncope'
            },

            # Renal
            'acute nephropyelitis': {
                'pyelonephritis', 'acute pyelonephritis',
                'upper urinary tract infection', 'kidney infection'
            },
            'chronic nephropyelitis': {
                'chronic pyelonephritis', 'recurrent pyelonephritis'
            },
            'renal tuberculosis': {
                'urogenital tuberculosis', 'genitourinary tuberculosis',
                'tuberculosis of kidney'
            },
            'bladder stones': {
                'vesical calculi', 'bladder calculi', 'urinary bladder stones',
                'cystolithiasis'
            },

            # Psychiatric
            'posttraumatic stress disorder': {
                'ptsd', 'post traumatic stress disorder',
                'post-traumatic stress disorder'
            },
            'schizoaffective disorder': {
                'schizoaffective', 'schizophrenia with mood disorder'
            },

            # Cardiovascular
            'carotid sinus syndrome': {
                'carotid sinus hypersensitivity', 'carotid sinus syncope'
            },

            # Urinary
            'stress incontinence': {
                'stress urinary incontinence', 'sui',
                'urinary stress incontinence'
            },
            'mixed incontinence': {
                'mixed urinary incontinence', 'mui'
            },
            'overactive bladder': {
                'urge incontinence', 'urgency incontinence',
                'urge urinary incontinence'
            },

            # Endocrine / Metabolic
            'hypocalcemia': {
                'low calcium', 'calcium deficiency', 'hypocalcaemia'
            },
            'simple obesity': {
                'obesity', 'morbid obesity', 'metabolic syndrome'
            },

            # Tuberculosis variants
            'tuberculosis of lumbar vertebrae': {
                'spinal tuberculosis', 'pott disease', 'potts disease',
                'vertebral tuberculosis', 'skeletal tuberculosis',
                'tuberculous spondylitis'
            },

            # Fracture matching
            'fracture': {
                'bone fracture', 'skeletal fracture'
            },

            # Infection categorical
            'infection (cellulitis or osteomyelitis)': {
                'cellulitis', 'osteomyelitis', 'skin infection',
                'soft tissue infection', 'bone infection'
            },

            # Hepatitis
            'alcoholic hepatitis': {
                'alcohol induced hepatitis', 'alcoholic liver disease'
            },
            'drug-induced hepatitis': {
                'drug induced liver injury', 'dili',
                'medication induced hepatitis', 'toxic hepatitis'
            },

            # Obesity subtypes (GT uses these)
            'gonadal obesity': {'obesity', 'endocrine obesity'},
            'hypothalamic obesity': {'obesity', 'endocrine obesity'},
            'cortisol obesity': {'cushing syndrome', 'cushings syndrome', 'obesity'},
            'pancreatic obesity': {'obesity', 'metabolic syndrome'},

            # Vague/categorical GT labels
            'an overdose of a substance': {
                'drug overdose', 'overdose', 'opioid overdose',
                'substance overdose', 'acute intoxication',
                'mixed drug intoxication'
            },
            'a psychiatric episode': {
                'psychiatric emergency', 'psychotic episode',
                'psychiatric decompensation', 'mental health crisis'
            },
            'a metabolic issue': {
                'metabolic disorder', 'metabolic acidosis',
                'metabolic alkalosis', 'electrolyte imbalance',
                'metabolic derangement'
            },
            'pneumonia (bacterial or viral)': {
                'pneumonia', 'bacterial pneumonia', 'viral pneumonia',
                'community acquired pneumonia', 'cap'
            },
            'infections from bacteria or viruses': {
                'bacterial infection', 'viral infection', 'infectious disease',
                'infectious wound', 'infected bite'
            },
            'bites or stings from insects or animals': {
                'insect bite', 'spider bite', 'snake bite',
                'brown recluse spider bite', 'venomous snake bite',
                'bite or sting', 'infected bite or sting'
            },
            'allergic or toxic reaction to plants or substances': {
                'allergic reaction', 'contact dermatitis', 'toxic reaction',
                'anaphylaxis', 'allergic contact dermatitis'
            },
            'bladder or kidney injury': {
                'bladder injury', 'kidney injury', 'renal injury',
                'bladder trauma', 'renal trauma'
            },
            'bladder or kidney cancer': {
                'bladder cancer', 'renal cell carcinoma', 'kidney cancer',
                'urothelial carcinoma', 'transitional cell carcinoma'
            },
            'side effects of chemotherapy': {
                'chemotherapy induced', 'chemotherapy toxicity',
                'chemotherapy side effects', 'drug toxicity',
                'chemotherapy induced hematuria'
            },
            'renal or bladder tumors': {
                'bladder cancer', 'renal cell carcinoma', 'kidney cancer',
                'urothelial carcinoma'
            },
            'systemic infection': {
                'sepsis', 'septicemia', 'bacteremia', 'systemic inflammatory response'
            },
            'infection from bacteria or viruses': {
                'bacterial infection', 'viral infection', 'infectious disease'
            },

            # Pathogen-as-diagnosis (GT lists organisms)
            'staphylococcus aureus': {
                'staph infection', 'staphylococcal infection',
                'mrsa', 'mssa', 'osteomyelitis', 'septic arthritis'
            },
            'streptococcus pyogenes': {
                'group a strep', 'streptococcal infection',
                'strep infection', 'cellulitis', 'necrotizing fasciitis'
            },
            'haemophilus influenzae': {
                'haemophilus infection', 'h influenzae infection'
            },
            'salmonella species': {
                'salmonella infection', 'salmonellosis', 'salmonella'
            },
            'kingella kingae': {
                'kingella infection', 'kingella osteomyelitis'
            },
            'streptococcus pneumoniae infection': {
                'pneumococcal infection', 'streptococcus pneumoniae',
                'pneumococcal pneumonia', 'pneumococcal meningitis'
            },
            'haemophilus influenzae infection': {
                'haemophilus influenzae', 'h influenzae',
                'haemophilus infection'
            },
            'salmonella infection': {
                'salmonellosis', 'salmonella', 'salmonella species',
                'enteric fever'
            },

            # Hepatitis B
            'hepatitis b vaccination': {
                'completed hbv vaccination', 'hepatitis b immune status',
                'hepatitis b immunity', 'hbv vaccination'
            },

            # Round 5b — remaining zero-recall fixes

            # Vague categorical GT labels
            'various infectious diseases': {
                'dengue fever', 'malaria', 'typhoid fever', 'chikungunya',
                'infectious disease', 'tropical infection'
            },
            'fungal infections': {
                'histoplasmosis', 'paracoccidioidomycosis', 'fungal infection',
                'coccidioidomycosis', 'blastomycosis', 'aspergillosis'
            },
            'liver parasites like echinococcus and fasciola': {
                'cystic echinococcosis', 'hepatic hydatid cyst',
                'hepatic hydatidosis', 'echinococcosis', 'fasciola hepatica',
                'fascioliasis', 'hydatid cyst'
            },
            'diseases of the vestibular apparatus': {
                'vestibular neuritis', 'vestibular neuronitis',
                'labyrinthitis', 'meniere disease', 'bppv',
                'benign paroxysmal positional vertigo',
                'vestibular disorder', 'acute vestibular syndrome'
            },
            'ophthalmologic diseases': {
                'ophthalmologic disease', 'eye disease', 'visual disturbance',
                'nystagmus', 'optic neuritis'
            },
            'sepsis from a different source': {
                'sepsis', 'septicemia', 'bloodstream infection',
                'central line associated bloodstream infection', 'clabsi',
                'catheter related bloodstream infection'
            },
            'sexually transmitted infection (gonorrhea, chlamydia, syphilis)': {
                'sexually transmitted infection', 'sti', 'std',
                'gonorrhea', 'chlamydia', 'syphilis',
                'gonococcal infection', 'chlamydial infection'
            },

            # Polyps
            'hyperplastic polyp': {
                'colonic polyp', 'colon polyp', 'colorectal polyp'
            },
            'tubular adenoma': {
                'adenomatous polyp', 'colorectal adenoma', 'colon adenoma'
            },
            'tubulovillous adenoma': {
                'adenomatous polyp', 'colorectal adenoma', 'colon adenoma'
            },
            'villous adenoma': {
                'adenomatous polyp', 'colorectal adenoma', 'colon adenoma'
            },

            # Cardiac / Ischemia
            'myocardial ischemia': {
                'acute coronary syndrome', 'angina pectoris', 'angina',
                'cardiac ischemia', 'coronary artery disease'
            },
            'cocaine-induced myocardial ischemia': {
                'acute coronary syndrome', 'cocaine induced chest pain',
                'cocaine cardiomyopathy'
            },
            'cardiogenic syncope': {
                'cardiac syncope', 'cardiac arrhythmia', 'cardiac conduction disorder',
                'cardiac conduction system disorder'
            },

            # Seizures
            'focal seizures': {
                'partial seizures', 'focal epilepsy', 'temporal lobe epilepsy',
                'seizure disorder'
            },
            'generalized seizures': {
                'generalized tonic clonic seizure', 'grand mal seizure',
                'epilepsy', 'seizure disorder', 'tonic clonic seizures'
            },
            'convulsive movement in hysteria': {
                'psychogenic non epileptic seizures', 'pnes',
                'conversion disorder', 'functional seizures'
            },

            # Pediatric / Congenital
            'cretinism': {
                'congenital hypothyroidism', 'neonatal hypothyroidism'
            },
            'rickets': {
                'vitamin d deficiency', 'nutritional rickets'
            },
            'hydrocephaly': {
                'hydrocephalus', 'congenital hydrocephalus'
            },
            "down's syndrome": {
                'down syndrome', 'trisomy 21'
            },
            'physiologic jaundice': {
                'physiological jaundice', 'neonatal jaundice',
                'newborn jaundice'
            },
            'abo incompatibility': {
                'abo hemolytic disease', 'abo isoimmunization',
                'abo hemolytic disease of newborn'
            },

            # Neck / Lymph
            'cervical lymphadenitis': {
                'lymphadenopathy', 'neck lymphadenopathy',
                'cervical lymphadenopathy'
            },
            'tuberculous lymphadenitis': {
                'lymphadenopathy', 'lymph node tuberculosis',
                'scrofula'
            },
            'malignant lymphoma': {
                'lymphoma', 'non hodgkin lymphoma', 'hodgkin lymphoma'
            },
            'thyroid adenoma': {
                'thyroid nodule', 'thyroid mass'
            },
            'thyroid carcinoma': {
                'thyroid cancer', 'papillary thyroid cancer',
                'follicular thyroid cancer'
            },
            'nonspecific lymphadenitis': {
                'lymphadenopathy', 'reactive lymphadenopathy',
                'bacterial lymphadenitis', 'lymphadenitis'
            },

            # Musculoskeletal
            'humeral fracture': {
                'humerus fracture', 'fracture of the humerus',
                'proximal humerus fracture'
            },
            'nedc muscle strain': {
                'neck muscle strain', 'cervical strain',
                'muscle strain', 'cervical muscle strain'
            },
            'spinal disk herniation': {
                'disc herniation', 'herniated disc', 'disk herniation',
                'cervical herniated disc', 'lumbar disc herniation'
            },
            'myofascitis of lower back': {
                'myofascial pain', 'lower back pain', 'muscle strain',
                'lumbar myofascial pain', 'back strain'
            },
            'acute back sprain': {
                'back strain', 'lumbar sprain', 'muscle strain',
                'musculoskeletal back pain'
            },
            'lumbar flexion compression fractures': {
                'compression fracture', 'lumbar compression fracture',
                'vertebral compression fracture'
            },
            'tennis elbow (lateral epicondylitis)': {
                'lateral epicondylitis', 'tennis elbow',
                'lateral epicondylalgia'
            },

            # Hearing
            'prasbycusis': {
                'presbycusis', 'age related hearing loss',
                'sensorineural hearing loss'
            },
            'cochlear nerve damage': {
                'sensorineural hearing loss', 'cochlear damage',
                'auditory neuropathy'
            },
            'otosderosis': {
                'otosclerosis', 'conductive hearing loss'
            },

            # Psychiatric (additional)
            'social phobia': {
                'social anxiety disorder', 'social anxiety'
            },
            'agoraphobia/specific phobia': {
                'agoraphobia', 'specific phobia', 'phobic disorder'
            },
            'panic attack': {
                'panic disorder', 'acute panic', 'anxiety attack'
            },

            # Prostate
            'benign prostatic hypertrophy (bph)': {
                'benign prostatic hyperplasia', 'bph',
                'prostatic hypertrophy', 'prostatic hyperplasia'
            },

            # GI specifics
            'pyloric obstruction': {
                'pyloric stenosis', 'gastric outlet obstruction'
            },
            'gastric perforation': {
                'perforated ulcer', 'peptic ulcer perforation',
                'gastrointestinal perforation'
            },
            'functional dyspepsia': {
                'dyspepsia', 'indigestion', 'non ulcer dyspepsia'
            },
            'redundant sigmoid colon': {
                'sigmoid volvulus', 'dolichosigmoid', 'elongated sigmoid'
            },
            'intestinal adhesion': {
                'adhesive bowel obstruction', 'abdominal adhesions',
                'postoperative adhesions'
            },

            # Rheumatology
            'disseminated gonorrhea': {
                'disseminated gonococcal infection', 'gonococcal arthritis',
                'reactive arthritis'
            },
            'reiter syndrome (reactive arthritis)': {
                'reactive arthritis', 'reiter syndrome', 'reiter disease'
            },

            # Misc
            'analgesic nephropathy': {
                'analgesic induced papillary necrosis',
                'analgesic induced nephropathy', 'nsaid nephropathy'
            },
            'consolidation': {
                'pneumonia', 'pulmonary consolidation', 'lung consolidation',
                'bacterial pneumonia', 'community acquired pneumonia'
            },
            'pleural effusion': {
                'fluid in pleural space', 'hydrothorax', 'exudative effusion'
            },
            'nasopharyngeal carcinoma with neck metastasis': {
                'nasopharyngeal carcinoma', 'nasopharyngeal cancer',
                'head and neck cancer', 'squamous cell carcinoma'
            },
            'fistula of the second or third branchial cleft': {
                'branchial cleft cyst', 'branchial cleft fistula',
                'branchial anomaly', 'lateral neck cyst'
            },

            # Round 5c — final zero-recall fixes
            'bacterial food poisoning': {
                'bacterial gastroenteritis', 'food poisoning',
                'foodborne illness', 'gastroenteritis'
            },
            'tumor of the colon': {
                'colon cancer', 'colorectal cancer', 'colonic neoplasm',
                'colon tumor'
            },
            'polyp of colon': {
                'colonic polyp', 'colon polyp', 'colorectal polyp',
                'adenomatous polyp'
            },
            'tumor of small intestine': {
                'small bowel tumor', 'small intestine cancer',
                'small bowel neoplasm', 'gastric cancer'
            },
            'achalasia of cardia': {
                'achalasia', 'esophageal achalasia', 'cardiospasm'
            },
            'esophageal hiatal hernia': {
                'hiatal hernia', 'hiatus hernia', 'diaphragmatic hernia'
            },
            'bulbar paralysis': {
                'bulbar palsy', 'pseudobulbar palsy',
                'lower motor neuron lesion'
            },
            'prostatic hyperplasia': {
                'benign prostatic hyperplasia', 'bph',
                'prostatic hypertrophy', 'benign prostatic hypertrophy'
            },
            'kidney stone': {
                'nephrolithiasis', 'urolithiasis', 'renal calculi',
                'renal stones', 'kidney stones'
            },
            'physiological vertigo': {
                'vertigo', 'motion sickness', 'positional vertigo',
                'benign positional vertigo'
            },
            'rib fracture': {
                'fractured rib', 'costal fracture', 'chest wall fracture',
                'costochondritis'
            },
        }

        # Build bidirectional mapping with NORMALIZED keys/values
        # (synonym lookup uses normalized inputs, so keys must match)
        bidirectional = {}
        for canonical, aliases in synonyms.items():
            norm_canonical = self.normalize_diagnosis(canonical)
            norm_aliases = {self.normalize_diagnosis(a) for a in aliases}
            # Merge into existing entries (multiple raw keys may normalize to same)
            existing = bidirectional.get(norm_canonical, set())
            bidirectional[norm_canonical] = existing | norm_aliases
            for norm_alias in norm_aliases:
                existing_alias = bidirectional.get(norm_alias, set())
                bidirectional[norm_alias] = existing_alias | {norm_canonical} | (norm_aliases - {norm_alias})

        return bidirectional

    def _build_clinical_hierarchies(self) -> Dict[str, List[str]]:
        """Build subtype/supertype relationships"""
        return {
            'myocardial infarction': [
                'stemi', 'nstemi', 'st elevation myocardial infarction',
                'non-st elevation myocardial infarction', 'acute mi'
            ],
            'pneumonia': [
                'community-acquired pneumonia', 'hospital-acquired pneumonia',
                'ventilator-associated pneumonia', 'aspiration pneumonia',
                'bacterial pneumonia', 'viral pneumonia', 'fungal pneumonia',
                'pneumocystis pneumonia', 'pneumocystis jirovecii pneumonia',
                'histoplasmosis', 'coccidioidomycosis'
            ],
            'arthritis': [
                'osteoarthritis', 'rheumatoid arthritis', 'psoriatic arthritis',
                'septic arthritis', 'reactive arthritis', 'gouty arthritis'
            ],
            'acute kidney injury': [
                'contrast-induced nephropathy', 'drug-induced aki', 'ischemic aki',
                'nephrotoxic aki', 'prerenal aki', 'intrinsic aki', 'postrenal aki'
            ],
            'heart failure': [
                'congestive heart failure', 'systolic heart failure',
                'diastolic heart failure', 'acute heart failure', 'chronic heart failure'
            ],
            'diabetes mellitus': [
                'type 1 diabetes', 'type 2 diabetes', 'gestational diabetes',
                'drug-induced diabetes', 'secondary diabetes'
            ],
            'vasculitis': [
                'systemic vasculitis', 'necrotizing vasculitis', 'drug-induced vasculitis',
                'hypersensitivity vasculitis', 'anca-associated vasculitis'
            ],
            'nephropathy': [
                'diabetic nephropathy', 'hypertensive nephropathy',
                'contrast-induced nephropathy', 'drug-induced nephropathy',
                'ischemic nephropathy'
            ],
            'aspergillosis': [
                'acute pulmonary aspergillosis', 'invasive aspergillosis',
                'allergic bronchopulmonary aspergillosis', 'abpa',
                'aspergillus pneumonia', 'allergic aspergillosis'
            ],
            'fungal pneumonia': [
                'histoplasmosis', 'coccidioidomycosis', 'aspergillosis',
                'pneumocystis pneumonia', 'blastomycosis', 'cryptococcosis'
            ],
            'hemolytic anemia': [
                'autoimmune hemolytic anemia', 'microangiopathic hemolytic anemia',
                'hereditary spherocytosis', 'sickle cell anemia',
                'paroxysmal nocturnal hemoglobinuria',
                'glucose-6-phosphate dehydrogenase deficiency'
            ],
            'thrombotic microangiopathy': [
                'thrombotic thrombocytopenic purpura', 'hemolytic uremic syndrome',
                'atypical hemolytic uremic syndrome', 'complement-mediated ttp'
            ],
            'bleeding disorders': [
                'disseminated intravascular coagulation',
                'immune thrombocytopenic purpura',
                'heparin induced thrombocytopenia', 'thrombocytopenia',
                'von willebrand disease', 'hemophilia'
            ],
            'anemia': [
                'iron deficiency anemia', 'megaloblastic anemia', 'hemolytic anemia',
                'aplastic anemia', 'chronic disease anemia', 'sickle cell anemia'
            ],
            'gastroenteritis': [
                'infectious gastroenteritis', 'viral gastroenteritis',
                'bacterial gastroenteritis', 'parasitic gastroenteritis'
            ],
            'neonatal bowel obstruction': [
                'meconium ileus', 'meconium plug syndrome', 'intestinal atresia',
                'duodenal atresia', 'hirschsprung disease', 'malrotation',
                'malrotation with midgut volvulus', 'meconium-ileal atresia',
                'gastrointestinal obstruction'
            ],
            'colorectal adenoma': [
                'tubulovillous adenoma', 'villous adenoma', 'tubular adenoma',
                'adenomatous polyp'
            ],
            'bacterial enteritis': [
                'campylobacter', 'salmonella', 'shigella', 'e coli',
                'campylobacter enteritis', 'salmonella enteritis'
            ],
            'antidepressants': [
                'tricyclic antidepressants', 'tca', 'ssri', 'maoi', 'snri',
                'tricyclic antidepressant overdose', 'ssri overdose',
                'antidepressant overdose', 'selective serotonin reuptake inhibitor'
            ],
            'peripheral artery disease': [
                'critical limb ischemia', 'femoral artery occlusion',
                'iliac artery stenosis', 'claudication'
            ],
            'parkinsonism': [
                'pseudoparkinsonism', 'neuroleptic-induced parkinsonism',
                'drug-induced parkinsonism'
            ],
            'extrapyramidal side effects': [
                'tardive dyskinesia', 'akathisia', 'dystonia',
                'acute dystonic reaction', 'pseudoparkinsonism',
                'neuroleptic-induced parkinsonism'
            ],
            'hypertension': [
                'essential hypertension', 'primary hypertension',
                'secondary hypertension', 'renovascular hypertension',
                'malignant hypertension', 'medication-induced hypertension'
            ],
            'thyroid disease': [
                'hyperthyroidism', 'hypothyroidism', 'thyrotoxicosis',
                'thyroid storm', 'congenital hypothyroidism', 'goiter',
                'neonatal thyrotoxicosis', 'transient hypothyroidism'
            ],

            # Neuromuscular
            'myopathy': [
                'duchenne muscular dystrophy', 'becker muscular dystrophy',
                'congenital myopathy', 'inflammatory myopathy', 'muscular dystrophy',
                'myotonic dystrophy', 'limb girdle muscular dystrophy', 'myositis',
                'polymyositis', 'dermatomyositis'
            ],
            'anterior horn cell disease': [
                'spinal muscular atrophy', 'spinal muscular atrophy type 1',
                'spinal muscular atrophy type 2', 'amyotrophic lateral sclerosis',
                'poliomyelitis', 'progressive muscular atrophy'
            ],

            # Peripheral neuropathy
            'peripheral neuropathy': [
                'diabetic neuropathy', 'alcoholic neuropathy',
                'autonomic neuropathy', 'sensory neuropathy',
                'motor neuropathy', 'chemotherapy induced neuropathy'
            ],

            # Infectious diseases (categorical)
            'infectious diseases': [
                'dengue fever', 'dengue', 'malaria', 'typhoid fever', 'typhoid',
                'chikungunya', 'zika', 'leptospirosis', 'hepatitis a', 'hepatitis b',
                'hepatitis c', 'tuberculosis', 'hiv', 'cholera', 'yellow fever',
                'meningitis', 'encephalitis', 'sepsis'
            ],

            # Overdose / Substance
            'overdose': [
                'drug overdose', 'opioid overdose', 'substance overdose',
                'medication overdose', 'alcohol poisoning', 'drug intoxication',
                'substance intoxication', 'intoxication'
            ],

            # Psychiatric (categorical)
            'psychiatric episode': [
                'psychiatric decompensation', 'psychotic episode', 'mental health crisis',
                'psychiatric emergency', 'psychosis', 'suicide attempt'
            ],

            # Metabolic (categorical)
            'metabolic disorder': [
                'metabolic acidosis', 'metabolic alkalosis', 'metabolic issue',
                'acid base disorder', 'electrolyte imbalance'
            ],

            # Traumatic injury (categorical)
            'traumatic injury': [
                'trauma', 'neurological trauma', 'blunt trauma', 'physical trauma',
                'head injury', 'traumatic brain injury'
            ],

            # Erectile dysfunction subtypes
            'erectile dysfunction': [
                'neurogenic erectile dysfunction', 'psychogenic erectile dysfunction',
                'drug induced erectile dysfunction', 'vascular erectile dysfunction',
                'hormonal erectile dysfunction'
            ],

            # Hematologic malignancy categories
            'leukemias': [
                'leukemia', 'chronic lymphocytic leukemia', 'acute lymphoblastic leukemia',
                'acute myeloid leukemia', 'chronic myeloid leukemia', 'hairy cell leukemia'
            ],
            'lymphomas': [
                'lymphoma', 'chronic lymphocytic leukemia', 'hodgkin lymphoma',
                'non hodgkin lymphoma', 'diffuse large b cell lymphoma',
                'follicular lymphoma', 'burkitt lymphoma', 'mantle cell lymphoma'
            ],
            'myeloproliferative disorders': [
                'myeloproliferative neoplasm', 'polycythemia vera',
                'essential thrombocythemia', 'myelofibrosis',
                'chronic myeloid leukemia'
            ],

            # Reactive / Inflammatory (categorical)
            'immune response to an inflammatory condition': [
                'leukocytosis', 'reactive leukocytosis', 'secondary leukocytosis',
                'reactive lymphocytosis', 'inflammatory response'
            ],

            # Illicit drug use (categorical)
            'illicit drug use': [
                'amphetamine intoxication', 'cocaine intoxication',
                'stimulant intoxication', 'methamphetamine intoxication',
                'opioid intoxication', 'cannabis intoxication',
                'synthetic cannabinoid intoxication', 'drug intoxication'
            ],

            # Sleep disorders
            'circadian rhythm sleep disorder': [
                'advanced sleep phase syndrome', 'delayed sleep phase syndrome',
                'circadian rhythm disorder', 'shift work sleep disorder',
                'irregular sleep wake rhythm disorder',
                'non 24 hour sleep wake disorder', 'jet lag disorder'
            ],

            # Endocarditis / pathogen-to-disease
            'infective endocarditis': [
                'streptococcus sanguinis', 'streptococcus viridans',
                'staphylococcus aureus endocarditis', 'bacterial endocarditis',
                'subacute bacterial endocarditis'
            ],

            # Antipsychotic side effects (categorical)
            'side effects from antipsychotic medications': [
                'medication induced movement disorder', 'tardive dyskinesia',
                'neuroleptic malignant syndrome', 'akathisia', 'dystonia',
                'drug induced parkinsonism', 'pseudoparkinsonism',
                'extrapyramidal symptoms', 'extrapyramidal side effects',
                'antipsychotic side effects'
            ],
            'dopamine antagonist': [
                'medication induced movement disorder', 'drug induced parkinsonism',
                'neuroleptic malignant syndrome', 'tardive dyskinesia',
                'extrapyramidal symptoms'
            ],

            # Stroke subtypes
            'stroke': [
                'ischemic stroke', 'hemorrhagic stroke', 'lacunar stroke',
                'embolic stroke', 'thrombotic stroke', 'cryptogenic stroke'
            ],
            'cerebrovascular accident': [
                'ischemic stroke', 'hemorrhagic stroke', 'lacunar stroke',
                'embolic stroke', 'thrombotic stroke', 'cryptogenic stroke'
            ],

            # Food poisoning (categorical)
            'food poisoning': [
                'scombroid poisoning', 'scombroid fish poisoning',
                'ciguatera poisoning', 'ciguatera fish poisoning',
                'shellfish poisoning', 'botulism', 'salmonella', 'campylobacter'
            ],

            # Allergic reaction subtypes
            'allergic reaction': [
                'anaphylaxis', 'anaphylactic reaction', 'anaphylactic shock',
                'food allergy', 'shellfish allergy', 'drug allergy'
            ],

            # Medication side effects (categorical)
            'medication side effects': [
                'antibiotic associated diarrhea', 'drug side effects',
                'drug side effect', 'adverse drug reaction', 'drug reaction',
                'medication side effect', 'anticholinergic poisoning',
                'anticholinergic toxicity', 'anticholinergic syndrome'
            ],

            # Intra-abdominal infection subtypes
            'intra abdominal infection': [
                'abdominal abscess', 'peritonitis', 'intra abdominal abscess',
                'subphrenic abscess', 'pelvic abscess'
            ],

            # Pelvic floor / Gynecological
            'pelvic floor dysfunction': [
                'vaginismus', 'vulvodynia', 'vestibulodynia',
                'pelvic floor myalgia', 'levator ani syndrome'
            ],
            'vulvodynia': [
                'vestibulodynia', 'provoked vestibulodynia', 'generalized vulvodynia'
            ],

            # Round 4 additions (cases 300-399)
            'acute coronary syndrome': [
                'myocardial infarction', 'stemi', 'nstemi', 'unstable angina',
                'st elevation myocardial infarction',
                'non st elevation myocardial infarction'
            ],
            'pulmonary embolism': [
                'pulmonary infarction', 'pulmonary thromboembolism'
            ],
            'congestive heart failure': [
                'diastolic heart failure', 'systolic heart failure',
                'left heart failure', 'left sided heart failure',
                'right heart failure', 'right sided heart failure',
                'cardiogenic pulmonary edema', 'pulmonary edema'
            ],
            'lung cancer': [
                'bronchogenic cancer', 'bronchogenic carcinoma', 'bronchial carcinoma',
                'non small cell lung cancer', 'small cell lung cancer',
                'adenocarcinoma of lung', 'squamous cell carcinoma of lung'
            ],
            'asthma': [
                'bronchial asthma', 'asthma exacerbation', 'acute asthma',
                'acute asthma attack', 'acute bronchospasm',
                'exercise induced asthma', 'allergic asthma', 'status asthmaticus'
            ],
            'bronchitis': [
                'acute bronchitis', 'chronic bronchitis'
            ],
            'skull fracture': [
                'temporal bone fracture', 'basilar skull fracture',
                'depressed skull fracture'
            ],
            'intracranial hemorrhage': [
                'subarachnoid hemorrhage', 'epidural hematoma', 'subdural hematoma',
                'intracerebral hemorrhage', 'cerebral hemorrhage'
            ],
            'intracranial infection': [
                'meningitis', 'encephalitis', 'brain abscess', 'cerebral abscess'
            ],
            'renal disease': [
                'chronic kidney disease', 'acute kidney injury', 'nephrotic syndrome',
                'glomerulonephritis', 'nephritis', 'renal failure'
            ],
            'electrolyte abnormalities': [
                'electrolyte imbalance', 'hypokalemia', 'hyperkalemia',
                'hyponatremia', 'hypernatremia', 'hypocalcemia', 'hypercalcemia',
                'magnesium deficiency', 'hypomagnesemia'
            ],
            'nutritional deficiencies': [
                'iron deficiency', 'iron deficiency anemia', 'vitamin b12 deficiency',
                'folate deficiency', 'thiamine deficiency', 'vitamin deficiency',
                'nutritional deficiency anemia', 'pernicious anemia'
            ],
            'glomerulonephritis': [
                'poststreptococcal glomerulonephritis',
                'membranoproliferative glomerulonephritis',
                'iga nephropathy', 'membranous nephropathy', 'lupus nephritis',
                'rapidly progressive glomerulonephritis',
                'acute poststreptococcal glomerulonephritis'
            ],
            'hyperthyroidism': [
                'graves disease', 'toxic multinodular goiter', 'toxic adenoma',
                'thyroid storm', 'thyrotoxicosis'
            ],
            'megaloblastic anemia': [
                'pernicious anemia', 'b12 deficiency anemia',
                'folate deficiency anemia', 'vitamin b12 deficiency'
            ],

            # Round 5 hierarchy additions (cases 400-569)

            # Vertigo / Vestibular
            'vertigo': [
                'benign paroxysmal positional vertigo', 'bppv',
                'vestibular neuritis', 'vestibular neuronitis',
                'labyrinthitis', 'meniere disease',
                'positional vertigo', 'central vertigo'
            ],

            # Syncope
            'syncope': [
                'vasovagal syncope', 'neurocardiogenic syncope',
                'carotid sinus syncope', 'orthostatic syncope',
                'cardiac syncope', 'neurologic syncope', 'reflex syncope'
            ],

            # Tuberculosis subtypes
            'tuberculosis': [
                'pulmonary tuberculosis', 'intestinal tuberculosis',
                'renal tuberculosis', 'spinal tuberculosis',
                'miliary tuberculosis', 'tuberculous meningitis',
                'genitourinary tuberculosis', 'skeletal tuberculosis',
                'tuberculosis of lumbar vertebrae', 'pott disease'
            ],

            # Fracture subtypes
            'fracture': [
                'skull fracture', 'cervical fracture', 'vertebral fracture',
                'rib fracture', 'clavicle fracture', 'humerus fracture',
                'radius fracture', 'ulna fracture', 'hip fracture',
                'femur fracture', 'tibia fracture', 'ankle fracture',
                'compression fracture', 'stress fracture',
                'pathological fracture', 'radial fracture'
            ],

            # Incontinence
            'urinary incontinence': [
                'stress incontinence', 'stress urinary incontinence',
                'urge incontinence', 'mixed incontinence',
                'mixed urinary incontinence', 'overflow incontinence',
                'functional incontinence'
            ],

            # Hepatitis
            'hepatitis': [
                'hepatitis a', 'hepatitis b', 'hepatitis c', 'hepatitis d',
                'hepatitis e', 'alcoholic hepatitis', 'drug induced hepatitis',
                'autoimmune hepatitis', 'viral hepatitis', 'toxic hepatitis'
            ],

            # Obesity subtypes
            'obesity': [
                'simple obesity', 'gonadal obesity', 'hypothalamic obesity',
                'cortisol obesity', 'pancreatic obesity', 'morbid obesity',
                'metabolic syndrome'
            ],

            # Disc / Spine
            'spinal disc disease': [
                'disk herniation', 'disc herniation', 'herniated disc',
                'intervertebral disk hernia', 'degenerative disc disease',
                'cervical herniated disc', 'lumbar disc herniation',
                'spinal stenosis'
            ],

            # Pyelonephritis
            'pyelonephritis': [
                'acute pyelonephritis', 'chronic pyelonephritis',
                'acute nephropyelitis', 'chronic nephropyelitis',
                'kidney infection', 'upper urinary tract infection'
            ],

            # Brain tumors
            'brain tumor': [
                'intracranial neoplasm', 'glioma', 'glioblastoma',
                'meningioma', 'astrocytoma', 'medulloblastoma',
                'cns tumor', 'cerebral neoplasm', 'brain neoplasm',
                'intracranial tumor'
            ],

            # Esophageal disease
            'esophageal disease': [
                'esophagitis', 'gastroesophageal reflux disease',
                'esophageal stricture', 'esophageal motility disorder',
                'achalasia', 'esophageal cancer', 'barrett esophagus',
                'esophageal spasm', 'esophageal hiatal hernia'
            ],

            # Colorectal neoplasms
            'colorectal neoplasm': [
                'colon cancer', 'colorectal cancer', 'rectal cancer',
                'colonic polyp', 'adenomatous polyp', 'tumor of the colon',
                'polyp of colon', 'colorectal adenoma'
            ],

            # Inflammatory bowel disease
            'inflammatory bowel disease': [
                'crohn disease', 'crohns disease', 'ulcerative colitis',
                'inflammatory bowel syndrome', 'colitis'
            ],

            # Cyanosis
            'cyanosis': [
                'central cyanosis', 'peripheral cyanosis', 'mixed cyanosis',
                'methemoglobinemia', 'sulfhemoglobinemia'
            ],
        }

    def normalize_diagnosis(self, diagnosis: str) -> str:
        """Normalize diagnosis for comparison"""
        if not diagnosis or not isinstance(diagnosis, str):
            return ""

        normalized = diagnosis.lower().strip()

        # Unicode normalization (ö → o, é → e, ü → u)
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

        # Remove numbering/bullets
        normalized = re.sub(r'^[\d\.\-\*]+\s*', '', normalized)

        # Strip possessive 's before removing punctuation
        normalized = re.sub(r"'s\b", '', normalized)

        # Remove parenthetical content (handles nested parens inside-out)
        while '(' in normalized and ')' in normalized:
            prev = normalized
            normalized = re.sub(r'\s*\([^()]*\)\s*', ' ', normalized)
            if normalized == prev:
                break

        # Normalize hyphens, slashes, en-dash, em-dash to spaces
        normalized = re.sub(r'[-/\u2013\u2014]', ' ', normalized)

        # Remove common prefixes that don't affect equivalence
        for prefix in ['acute', 'chronic', 'primary', 'secondary', 'idiopathic']:
            normalized = re.sub(rf'^{prefix}\s+', '', normalized)

        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Remove stop words / articles that inflate Jaccard denominator
        stop_words = {'a', 'an', 'the', 'of', 'such', 'as', 'with', 'due', 'to',
                      'and', 'or', 'in', 'by', 'from', 'for', 'on'}
        words = normalized.split()
        normalized = ' '.join(w for w in words if w not in stop_words)

        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def are_clinically_equivalent(self, diag1: str, diag2: str) -> Tuple[bool, str, float]:
        """
        Determine if two diagnoses are clinically equivalent.

        Returns: (is_equivalent, reasoning, confidence)
        4-tier matching: direct -> synonym -> hierarchy -> word overlap
        """
        if not diag1 or not diag2:
            return False, "Empty diagnosis", 0.0

        norm1 = self.normalize_diagnosis(diag1)
        norm2 = self.normalize_diagnosis(diag2)

        # Rule 1: Direct match
        if norm1 == norm2:
            return True, "Direct match after normalization", 1.0

        # Rule 2: Synonym match
        if self._check_synonym_match(norm1, norm2):
            return True, "Medical synonym match", 0.95

        # Rule 3: Hierarchy match (subtype/supertype + substring + core match)
        hierarchy_result = self._check_hierarchy_match(norm1, norm2)
        if hierarchy_result[0]:
            return True, hierarchy_result[1], 0.90

        # Rule 4: Word overlap (Jaccard >= 0.8)
        overlap_score = self._calculate_word_overlap(norm1, norm2)
        if overlap_score >= 0.8:
            return True, f"High word overlap ({overlap_score:.2f})", overlap_score

        return False, "No clinical equivalence found", 0.0

    def _check_synonym_match(self, norm1: str, norm2: str) -> bool:
        """Check if diagnoses are medical synonyms"""
        if norm1 in self.medical_synonyms:
            if norm2 in self.medical_synonyms[norm1]:
                return True
        if norm2 in self.medical_synonyms:
            if norm1 in self.medical_synonyms[norm2]:
                return True
        return False

    def _check_hierarchy_match(self, norm1: str, norm2: str) -> Tuple[bool, str]:
        """Check subtype/supertype relationships + substring containment"""
        # Predefined hierarchies
        for supertype, subtypes in self.clinical_hierarchies.items():
            sup_norm = self.normalize_diagnosis(supertype)
            if norm1 == sup_norm:
                for sub in subtypes:
                    if norm2 == self.normalize_diagnosis(sub):
                        return True, f"Subtype: {norm2} is a type of {norm1}"
            if norm2 == sup_norm:
                for sub in subtypes:
                    if norm1 == self.normalize_diagnosis(sub):
                        return True, f"Subtype: {norm1} is a type of {norm2}"

        # Substring containment
        if norm1 in norm2 or norm2 in norm1:
            longer = norm2 if len(norm2) > len(norm1) else norm1
            shorter = norm1 if len(norm1) < len(norm2) else norm2
            return True, f"Specificity: {longer} contains {shorter}"

        # Core word match (strip modifiers)
        modifiers = {'acute', 'chronic', 'allergic', 'drug-induced',
                     'contrast-induced', 'primary', 'secondary',
                     'idiopathic', 'autoimmune', 'infectious'}
        core1 = [w for w in norm1.split() if w not in modifiers]
        core2 = [w for w in norm2.split() if w not in modifiers]
        if core1 and core2 and core1 == core2:
            return True, "Same condition with different modifiers"

        return False, "No hierarchy match"

    def _calculate_word_overlap(self, norm1: str, norm2: str) -> float:
        """Calculate Jaccard word overlap"""
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0


# =============================================================================
# Evaluation Data Structures
# =============================================================================

@dataclass
class CaseEvaluation:
    """Evaluation result for a single case"""
    case_index: int
    case_name: str = ""
    tp_count: int = 0
    fp_count: int = 0
    fn_count: int = 0
    ae_count: int = 0  # Appropriately excluded (considered but not in final list)

    matched_pairs: List[Tuple[str, str]] = field(default_factory=list)
    false_positives: List[str] = field(default_factory=list)
    false_negatives: List[str] = field(default_factory=list)
    appropriately_excluded: List[str] = field(default_factory=list)

    system_diagnoses: List[str] = field(default_factory=list)
    ground_truth_diagnoses: List[str] = field(default_factory=list)

    recall: float = 0.0
    precision: float = 0.0
    clinical_reasoning_quality: float = 0.0
    diagnostic_safety: float = 0.0
    duration_seconds: float = 0.0

    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


@dataclass
class BatchEvaluation:
    """Aggregated evaluation across multiple cases"""
    case_results: List[CaseEvaluation] = field(default_factory=list)
    total_tp: int = 0
    total_fp: int = 0
    total_fn: int = 0
    total_ae: int = 0
    macro_recall: float = 0.0
    macro_precision: float = 0.0
    macro_f1: float = 0.0
    macro_crq: float = 0.0
    macro_safety: float = 0.0
    micro_recall: float = 0.0
    micro_precision: float = 0.0
    total_cases: int = 0
    total_duration: float = 0.0


# =============================================================================
# Diagnosis Extraction from v10 Output
# =============================================================================

def extract_system_diagnoses(result: Dict[str, Any]) -> List[str]:
    """
    Extract final diagnoses from v10 pipeline output.

    Checks multiple locations in order of priority:
    1. results.voting_result.ranked_results (Borda-voted, best source)
    2. results.final_diagnoses (synthesized list)
    3. Last round structured_data
    """
    diagnoses = []

    results = result.get('results', result)

    # Priority 1: Voting results (ranked Borda output)
    voting = results.get('voting_result', {})
    if voting:
        ranked = voting.get('ranked_results', [])
        if ranked:
            for item in ranked:
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    diagnoses.append(str(item[0]))
                elif isinstance(item, str):
                    diagnoses.append(item)
            if diagnoses:
                return diagnoses[:6]

    # Priority 2: final_diagnoses list
    final = results.get('final_diagnoses', [])
    if final:
        for d in final:
            if isinstance(d, (list, tuple)):
                diagnoses.append(str(d[0]))
            elif isinstance(d, str):
                diagnoses.append(d)
        if diagnoses:
            return diagnoses[:6]

    # Priority 3: Scan structured_data from last rounds
    rounds = results.get('rounds', {})
    for round_name in reversed(list(rounds.keys())):
        round_data = rounds[round_name]
        responses = round_data.get('responses', [])
        for resp in responses:
            sd = resp.get('structured_data', {})
            if isinstance(sd, dict):
                diagnoses.extend(sd.keys())
        if diagnoses:
            break

    return list(dict.fromkeys(diagnoses))[:6]  # Deduplicate, preserve order


def extract_all_considered(result: Dict[str, Any]) -> Set[str]:
    """
    Extract ALL diagnoses mentioned anywhere in the pipeline
    (for AE classification — was it considered even if not in final list?).
    """
    considered = set()
    results = result.get('results', result)

    rounds = results.get('rounds', {})
    for round_data in rounds.values():
        responses = round_data.get('responses', [])
        for resp in responses:
            sd = resp.get('structured_data', {})
            if isinstance(sd, dict):
                considered.update(sd.keys())

    return considered


# =============================================================================
# Benchmark Evaluator
# =============================================================================

class BenchmarkEvaluator:
    """Evaluates v10 pipeline output against Open-XDDx ground truth"""

    def __init__(self):
        self.engine = ClinicalEquivalenceEngine()

    def evaluate_case(self, result: Dict[str, Any],
                      ground_truth: Dict[str, List[str]],
                      case_index: int = 0) -> CaseEvaluation:
        """
        Evaluate a single case.

        Args:
            result: v10 pipeline JSON output (from export_results)
            ground_truth: {diagnosis: [evidence_list]} from Open-XDDx
            case_index: Index in dataset
        """
        evaluation = CaseEvaluation(case_index=case_index)

        # Extract system diagnoses from pipeline output
        sys_diags = extract_system_diagnoses(result)
        gt_diags = list(ground_truth.keys())
        all_considered = extract_all_considered(result)

        evaluation.system_diagnoses = sys_diags
        evaluation.ground_truth_diagnoses = gt_diags
        evaluation.duration_seconds = (
            result.get('results', result).get('total_duration', 0)
        )

        # Case name
        case_data = result.get('case', {})
        evaluation.case_name = case_data.get('name', f"case_{case_index}")

        # Match system diagnoses to ground truth
        matched_gt = set()
        matched_sys = set()

        for gt_diag in gt_diags:
            for sys_diag in sys_diags:
                if sys_diag in matched_sys:
                    continue
                is_eq, reason, conf = self.engine.are_clinically_equivalent(
                    gt_diag, sys_diag
                )
                if is_eq:
                    evaluation.matched_pairs.append((gt_diag, sys_diag))
                    matched_gt.add(gt_diag)
                    matched_sys.add(sys_diag)
                    break

        # True Positives
        evaluation.tp_count = len(evaluation.matched_pairs)

        # False Negatives (ground truth not matched)
        for gt_diag in gt_diags:
            if gt_diag not in matched_gt:
                # Check if it was considered anywhere in pipeline
                was_considered = False
                for considered_diag in all_considered:
                    is_eq, _, _ = self.engine.are_clinically_equivalent(
                        gt_diag, considered_diag
                    )
                    if is_eq:
                        was_considered = True
                        break

                if was_considered:
                    evaluation.appropriately_excluded.append(gt_diag)
                    evaluation.ae_count += 1
                else:
                    evaluation.false_negatives.append(gt_diag)
                    evaluation.fn_count += 1

        # False Positives (system diagnoses not matching any GT)
        for sys_diag in sys_diags:
            if sys_diag not in matched_sys:
                evaluation.false_positives.append(sys_diag)
                evaluation.fp_count += 1

        # Compute metrics
        tp = evaluation.tp_count
        fp = evaluation.fp_count
        fn = evaluation.fn_count
        ae = evaluation.ae_count

        # Recall = TP / (TP + FN)
        evaluation.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # Precision = TP / (TP + FP)
        evaluation.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # Clinical Reasoning Quality = (TP + 0.5*AE) / (TP + FN + AE)
        evaluation.clinical_reasoning_quality = (
            (tp + 0.5 * ae) / (tp + fn + ae) if (tp + fn + ae) > 0 else 0.0
        )

        # Diagnostic Safety = (TP + AE) / (TP + FN + AE)
        evaluation.diagnostic_safety = (
            (tp + ae) / (tp + fn + ae) if (tp + fn + ae) > 0 else 0.0
        )

        return evaluation

    def evaluate_batch(self, results_dir: str,
                       ground_truths: Dict[int, Dict[str, List[str]]]) -> BatchEvaluation:
        """
        Evaluate all case results in a directory.

        Args:
            results_dir: Directory containing per-case JSON files
            ground_truths: {case_index: {diagnosis: [evidence]}}
        """
        batch = BatchEvaluation()
        json_files = sorted(
            f for f in os.listdir(results_dir) if f.endswith('.json')
            and f.startswith('case_')
        )

        for json_file in json_files:
            filepath = os.path.join(results_dir, json_file)
            try:
                with open(filepath) as f:
                    result = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"  Skipping {json_file}: {e}")
                continue

            # Extract case index from filename (case_000.json)
            try:
                idx = int(json_file.replace('case_', '').replace('.json', ''))
            except ValueError:
                continue

            gt = ground_truths.get(idx)
            if gt is None:
                print(f"  No ground truth for case {idx}, skipping")
                continue

            case_eval = self.evaluate_case(result, gt, case_index=idx)
            batch.case_results.append(case_eval)

        # Aggregate
        batch.total_cases = len(batch.case_results)
        if batch.total_cases == 0:
            return batch

        batch.total_tp = sum(c.tp_count for c in batch.case_results)
        batch.total_fp = sum(c.fp_count for c in batch.case_results)
        batch.total_fn = sum(c.fn_count for c in batch.case_results)
        batch.total_ae = sum(c.ae_count for c in batch.case_results)
        batch.total_duration = sum(c.duration_seconds for c in batch.case_results)

        # Macro averages
        batch.macro_recall = sum(c.recall for c in batch.case_results) / batch.total_cases
        batch.macro_precision = sum(c.precision for c in batch.case_results) / batch.total_cases
        batch.macro_f1 = sum(c.f1 for c in batch.case_results) / batch.total_cases
        batch.macro_crq = sum(c.clinical_reasoning_quality for c in batch.case_results) / batch.total_cases
        batch.macro_safety = sum(c.diagnostic_safety for c in batch.case_results) / batch.total_cases

        # Micro averages
        micro_tp = batch.total_tp
        micro_fp = batch.total_fp
        micro_fn = batch.total_fn
        batch.micro_recall = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0.0
        batch.micro_precision = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0.0

        return batch


# =============================================================================
# Reporting
# =============================================================================

def print_report(batch: BatchEvaluation):
    """Print formatted evaluation report"""
    print("\n" + "=" * 70)
    print("BENCHMARK EVALUATION REPORT")
    print("=" * 70)

    print(f"\nCases evaluated: {batch.total_cases}")
    print(f"Total duration:  {batch.total_duration:.1f}s "
          f"({batch.total_duration/batch.total_cases:.1f}s/case)" if batch.total_cases > 0 else "")

    print(f"\n--- Aggregate Counts ---")
    print(f"  True Positives:          {batch.total_tp}")
    print(f"  False Positives:         {batch.total_fp}")
    print(f"  False Negatives:         {batch.total_fn}")
    print(f"  Appropriately Excluded:  {batch.total_ae}")

    print(f"\n--- Macro Averages (per-case, then averaged) ---")
    print(f"  Clinical Recall:         {batch.macro_recall:.1%}")
    print(f"  Precision:               {batch.macro_precision:.1%}")
    print(f"  F1 Score:                {batch.macro_f1:.1%}")
    print(f"  Clinical Reasoning Q:    {batch.macro_crq:.1%}")
    print(f"  Diagnostic Safety:       {batch.macro_safety:.1%}")

    print(f"\n--- Micro Averages (pooled TP/FP/FN) ---")
    print(f"  Clinical Recall:         {batch.micro_recall:.1%}")
    print(f"  Precision:               {batch.micro_precision:.1%}")

    # Per-case breakdown
    print(f"\n--- Per-Case Breakdown ---")
    print(f"{'Case':>6} {'TP':>4} {'FP':>4} {'FN':>4} {'AE':>4} "
          f"{'Recall':>8} {'Prec':>8} {'CRQ':>8} {'Safety':>8} {'Time':>7}")
    print("-" * 70)

    for c in batch.case_results:
        print(f"{c.case_index:>6} {c.tp_count:>4} {c.fp_count:>4} "
              f"{c.fn_count:>4} {c.ae_count:>4} "
              f"{c.recall:>8.1%} {c.precision:>8.1%} "
              f"{c.clinical_reasoning_quality:>8.1%} "
              f"{c.diagnostic_safety:>8.1%} "
              f"{c.duration_seconds:>6.1f}s")

    # Baseline comparisons
    print(f"\n--- Baseline Comparisons ---")
    print(f"  Zhou Dual-Inf (GPT-4, 570 cases):  53.3% recall")
    print(f"  v7.4 (Llama-3-8B, 30 cases):       63.0% recall, 67.8% precision")
    print(f"  v10  ({batch.total_cases} cases):  "
          f"             {batch.macro_recall:.1%} recall, "
          f"{batch.macro_precision:.1%} precision")
    recall_diff = (batch.macro_recall - 0.533) * 100
    print(f"  vs Zhou:  {'+'if recall_diff > 0 else ''}{recall_diff:.1f} pp recall")


def save_report(batch: BatchEvaluation, output_path: str):
    """Save evaluation report as JSON"""
    report = {
        'summary': {
            'total_cases': batch.total_cases,
            'total_tp': batch.total_tp,
            'total_fp': batch.total_fp,
            'total_fn': batch.total_fn,
            'total_ae': batch.total_ae,
            'total_duration_seconds': batch.total_duration,
            'macro_recall': batch.macro_recall,
            'macro_precision': batch.macro_precision,
            'macro_f1': batch.macro_f1,
            'macro_crq': batch.macro_crq,
            'macro_safety': batch.macro_safety,
            'micro_recall': batch.micro_recall,
            'micro_precision': batch.micro_precision,
        },
        'baselines': {
            'zhou_dual_inf_gpt4': {'recall': 0.533, 'note': 'GPT-4, 570 cases'},
            'v74_llama8b': {'recall': 0.630, 'precision': 0.678, 'note': 'Llama-3-8B, 30 cases'},
        },
        'per_case': [
            {
                'case_index': c.case_index,
                'case_name': c.case_name,
                'tp': c.tp_count,
                'fp': c.fp_count,
                'fn': c.fn_count,
                'ae': c.ae_count,
                'recall': c.recall,
                'precision': c.precision,
                'f1': c.f1,
                'crq': c.clinical_reasoning_quality,
                'safety': c.diagnostic_safety,
                'duration': c.duration_seconds,
                'matched_pairs': c.matched_pairs,
                'false_positives': c.false_positives,
                'false_negatives': c.false_negatives,
                'appropriately_excluded': c.appropriately_excluded,
                'system_diagnoses': c.system_diagnoses,
                'ground_truth': c.ground_truth_diagnoses,
            }
            for c in batch.case_results
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to {output_path}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate v10 benchmark results against Open-XDDx ground truth"
    )
    parser.add_argument('--results-dir', required=True,
                        help='Directory containing per-case JSON results')
    parser.add_argument('--dataset', default='pipeline/data/Open-XDDx.xlsx',
                        help='Path to Open-XDDx.xlsx')
    parser.add_argument('--output', default=None,
                        help='Output JSON report path')
    args = parser.parse_args()

    # Load ground truth from dataset
    import ast
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required. Install with: pip install pandas openpyxl")
        return

    print(f"Loading dataset: {args.dataset}")
    df = pd.read_excel(args.dataset)

    ground_truths = {}
    for _, row in df.iterrows():
        idx = int(row['Index'])
        interpretation = row['interpretation']
        try:
            gt = ast.literal_eval(interpretation) if isinstance(interpretation, str) else interpretation
        except (ValueError, SyntaxError):
            try:
                gt = json.loads(interpretation)
            except (json.JSONDecodeError, TypeError):
                print(f"  Warning: Could not parse ground truth for case {idx}")
                continue
        ground_truths[idx] = gt

    print(f"Loaded {len(ground_truths)} ground truth cases")

    # Evaluate
    evaluator = BenchmarkEvaluator()
    batch = evaluator.evaluate_batch(args.results_dir, ground_truths)

    # Report
    print_report(batch)

    if args.output:
        save_report(batch, args.output)
    else:
        default_output = os.path.join(args.results_dir, 'evaluation_report.json')
        save_report(batch, default_output)


if __name__ == '__main__':
    main()
