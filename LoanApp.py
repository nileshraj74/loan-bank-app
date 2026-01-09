import streamlit as st
import pandas as pd

# ---------------- CONFIG ----------------
EXCEL_PATH = "Bank_Calc.xlsx"

st.set_page_config(page_title="Loan Bank Eligibility Engine", layout="wide")
st.title("🏦 Loan Bank Eligibility Analyzer")

# ---------------- LOAD BANK RULES ----------------
@st.cache_data
def load_bank_rules():
    df = pd.read_excel(EXCEL_PATH)

    # --- Clean column names ---
    df.columns = df.columns.astype(str).str.strip()

    # --- Auto-detect first column as Criteria (even if misspelled) ---
    criteria_col = df.columns[0]
    df.set_index(criteria_col, inplace=True)

    # --- Clean criteria names ---
    df.index = df.index.astype(str).str.strip()

    # --- Normalize percentage values ---
    def normalize(val):
        if isinstance(val, str) and "%" in val:
            return float(val.replace("%", "").strip()) / 100
        return val

    df = df.applymap(normalize)

    return df

rules_df = load_bank_rules()
banks = rules_df.columns.tolist()

# ---------------- USER INPUTS ----------------
st.header("📥 Enter Proposal Details")

col1, col2, col3 = st.columns(3)

with col1:
    primary_security = st.selectbox("Primary Security", ["Yes", "No"])
    prim_sec_age = st.selectbox(
        "Purchase Time of Primary Security",
        ["Within 1 Year", "Between 1-2 Years", "Before 2 Years"]
    )

    land_cost = st.number_input("Land Cost (₹)", min_value=0.0)
    land_loan = st.number_input("Loan for Land Purchase (₹)", min_value=0.0)

    construction_cost = st.number_input("Construction Cost (₹)", min_value=0.0)
    construction_loan = st.number_input("Loan for Construction (₹)", min_value=0.0)

with col2:
    machinery_cost = st.number_input("Machinery Cost (₹)", min_value=0.0)
    machinery_loan = st.number_input("Loan for Machinery (₹)", min_value=0.0)

    utility_cost = st.number_input("Utility Cost (₹)", min_value=0.0)
    utility_loan = st.number_input("Loan for Utilities (₹)", min_value=0.0)

    contingencies = st.number_input("Contingencies (₹)", min_value=0.0)
    other_loan = st.number_input("Loan for Other Expenses (₹)", min_value=0.0)

with col3:
    cc_requirement = st.number_input("CC Requirement (₹)", min_value=0.0)

    other_sec_value = st.number_input("Market Value of Other Security (₹)", min_value=0.0)
    other_sec_age = st.selectbox(
        "Purchase Time of Other Security",
        ["Within 1 Year", "Between 1-2 Years", "Before 2 Years"]
    )

    expected_roi = st.number_input("Expected ROI (%)", min_value=0.0)
    expected_pf = st.number_input("Expected Processing Fees (%)", min_value=0.0)
    margin_value = st.number_input("Promoter Own Fund + USL (₹)", min_value=0.0)

# ---------------- AUTO CALCULATIONS ----------------
project_cost = land_cost + construction_cost + machinery_cost + utility_cost + contingencies

required_total_loan = (
        land_loan + construction_loan + machinery_loan +
        utility_loan + other_loan + cc_requirement
)

st.subheader("📊 Calculated Values")
st.write(f"**Project Cost:** ₹ {project_cost:,.0f}")
st.write(f"**Required Total Loan:** ₹ {required_total_loan:,.0f}")

# ---------------- BANK EVALUATION ----------------
if st.button("🚀 ShowMeTheBanks"):

    eligible_banks = []
    rejected_banks = []

    for bank in banks:
        reason = ""

        MinSec = rules_df.at["MinSec", bank]
        HighROI = rules_df.at["HighROI", bank]
        LowROI = rules_df.at["LowROI", bank]
        Min_PF = rules_df.at["Min_PF", bank]
        Max_PF = rules_df.at["Max_PF", bank]

        Margin4Land = rules_df.at["Margin4LandPurchaseTL", bank]
        Margin4Cons = rules_df.at["Margin4ConstructionTL", bank]
        Margin4MTL = rules_df.at["Margin4MTL", bank]
        Margin4Util = rules_df.at["Margin4UtilitiesTL", bank]
        Margin4OTL = rules_df.at["Margin4OTL", bank]

        # ---- Security Value ----
        if primary_security == "No":
            security_value = land_cost + construction_cost + other_sec_value
        else:
            security_value = other_sec_value

        security_coverage = security_value / required_total_loan if required_total_loan else 0

        if security_coverage < MinSec:
            rejected_banks.append((bank, "Insufficient Security Coverage"))
            continue

        # ---- Margin Check ----
        margin_required = (
                Margin4Land * land_loan +
                Margin4Cons * construction_loan +
                Margin4MTL * machinery_loan +
                Margin4Util * utility_loan +
                Margin4OTL * other_loan
        )

        if margin_value < margin_required:
            rejected_banks.append((bank, "Insufficient Margin"))
            continue

        # ---- ROI Check ----
        expected_roi_decimal = expected_roi / 100

        if not (LowROI <= expected_roi_decimal):
            rejected_banks.append((bank, "ROI Not in Range"))
            continue

        # ---- PF Check ----
        expected_pf_decimal = expected_pf / 100

        if not (Min_PF <= expected_pf_decimal):
            rejected_banks.append((bank, "Processing Fee Not in Range"))
            continue

        eligible_banks.append(bank)

    # ---------------- RESULTS ----------------
    st.header("✅ Eligible Banks")
    if eligible_banks:
        for b in eligible_banks:
            st.success(f"This proposal can be put in **{b} Bank**")
    else:
        st.warning("No banks matched the eligibility.")

    st.header("❌ Rejected Banks")
    for b, r in rejected_banks:
        st.error(f"{b}: {r}")
