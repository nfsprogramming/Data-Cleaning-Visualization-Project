"""
Data Cleaning & Visualization Project

This script demonstrates a comprehensive data cleaning workflow followed by
meaningful visualizations using Python pandas and matplotlib.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_paths():
    """Setup project paths using pathlib for cross-platform compatibility."""
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = BASE_DIR / "outputs"
    
    # Create directories if they don't exist
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    return BASE_DIR, DATA_DIR, OUTPUT_DIR


def load_data(data_dir: Path) -> pd.DataFrame:
    """Load the raw dataset with validation."""
    raw_data_path = data_dir / "raw_dataset.csv"
    
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {raw_data_path}")
    
    logger.info(f"Loading dataset from {raw_data_path}")
    df = pd.read_csv(raw_data_path)
    
    logger.info(f"Initial dataset shape: {df.shape}")
    logger.info(f"Initial columns: {list(df.columns)}")
    
    return df


def validate_data(df: pd.DataFrame) -> None:
    """Validate dataset structure and contents."""
    logger.info("Validating dataset...")
    
    if df.empty:
        raise ValueError("Dataset is empty")
    
    required_columns = ['Age', 'Salary', 'Department', 'Experience']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Dataset validation passed. Rows: {len(df)}, Columns: {len(df.columns)}")


def analyze_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze and report missing values."""
    logger.info("Analyzing missing values...")
    
    missing_counts = df.isnull().sum()
    missing_percentages = (missing_counts / len(df)) * 100
    
    missing_report = pd.DataFrame({
        'Column': df.columns,
        'Missing_Count': missing_counts.values,
        'Missing_Percentage': missing_percentages.values
    })
    
    total_missing = missing_counts.sum()
    logger.info(f"Total missing values: {total_missing}")
    logger.info(f"Missing values by column:\n{missing_report.to_string(index=False)}")
    
    return missing_report


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values with appropriate strategies."""
    logger.info("Handling missing values...")
    
    initial_rows = len(df)
    
    # Numeric columns: fill with median
    df['Age'] = df['Age'].fillna(df['Age'].median())
    df['Salary'] = df['Salary'].fillna(df['Salary'].median())
    
    # Categorical columns: fill with 'Unknown'
    df['Department'] = df['Department'].fillna('Unknown')
    
    logger.info(f"Missing values handled. Rows remain: {len(df)}")
    
    return df


def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Detect and remove duplicate rows."""
    logger.info("Checking for duplicates...")
    
    initial_rows = len(df)
    duplicate_count = df.duplicated().sum()
    
    logger.info(f"Rows before duplicate removal: {initial_rows}")
    logger.info(f"Duplicate rows detected: {duplicate_count}")
    
    if duplicate_count > 0:
        df = df.drop_duplicates().copy()
        logger.info(f"Rows after duplicate removal: {len(df)}")
    else:
        logger.info("No duplicates found")
    
    return df


def detect_outliers_iqr(df: pd.DataFrame, column: str) -> tuple:
    """Detect outliers using IQR method."""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    
    return outliers, lower_bound, upper_bound


def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Handle outliers using IQR method for numeric columns."""
    logger.info("Detecting outliers using IQR method...")
    
    initial_rows = len(df)
    outlier_report = []
    
    for column in ['Age', 'Salary']:
        outliers, lower_bound, upper_bound = detect_outliers_iqr(df, column)
        
        if len(outliers) > 0:
            logger.info(f"Outliers detected in {column}: {len(outliers)} rows")
            logger.info(f"  IQR bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
            logger.info(f"  Outlier values: {outliers[column].tolist()}")
            
            outlier_report.append({
                'Column': column,
                'Outlier_Count': len(outliers),
                'Lower_Bound': lower_bound,
                'Upper_Bound': upper_bound
            })
    
    # Remove outliers
    for column in ['Age', 'Salary']:
        _, lower_bound, upper_bound = detect_outliers_iqr(df, column)
        df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    
    final_rows = len(df)
    rows_removed = initial_rows - final_rows
    
    logger.info(f"Outlier handling complete. Rows removed: {rows_removed}")
    logger.info(f"Final rows after outlier removal: {final_rows}")
    
    return df, outlier_report, rows_removed


def create_cleaning_summary(
    initial_rows: int, 
    final_rows: int, 
    duplicate_count: int, 
    outlier_rows_removed: int,
    output_dir: Path
) -> None:
    """Create and save a comprehensive cleaning summary."""
    logger.info("Creating cleaning summary...")
    
    summary_data = {
        'Metric': [
            'Initial Rows',
            'After Duplicate Removal',
            'After Missing Value Handling',
            'After Outlier Filtering',
            'Final Rows',
            'Total Rows Removed',
            'Duplicate Rows Removed',
            'Outlier Rows Removed'
        ],
        'Count': [
            initial_rows,
            initial_rows - duplicate_count,
            initial_rows - duplicate_count,  # Missing value handling doesn't remove rows
            final_rows,
            final_rows,
            initial_rows - final_rows,
            duplicate_count,
            outlier_rows_removed
        ],
        'Reason': [
            'Original dataset',
            'Duplicate rows removed',
            'Missing values filled (no rows removed)',
            'Statistical outliers removed using IQR method',
            'Final cleaned dataset',
            'Total rows removed during cleaning',
            'Exact duplicate records',
            'Values outside 1.5*IQR range (Age, Salary)'
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_path = output_dir / "cleaning_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    
    logger.info(f"Cleaning summary saved to {summary_path}")
    logger.info(f"\nCleaning Summary:\n{summary_df.to_string(index=False)}")


def create_visualizations(df: pd.DataFrame, output_dir: Path) -> None:
    """Create portfolio-quality visualizations."""
    logger.info("Creating visualizations...")
    
    # Set style for better aesthetics
    plt.style.use('seaborn-v0_8')
    
    # 1. Missing Values Overview (before cleaning would be ideal, but showing current state)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Data Cleaning & Analysis Results', fontsize=16, fontweight='bold')
    
    # Salary Distribution
    axes[0, 0].hist(df['Salary'], bins=10, edgecolor='black', alpha=0.7, color='steelblue')
    axes[0, 0].set_title('Salary Distribution', fontweight='bold')
    axes[0, 0].set_xlabel('Salary ($)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Age Distribution
    axes[0, 1].hist(df['Age'], bins=8, edgecolor='black', alpha=0.7, color='coral')
    axes[0, 1].set_title('Age Distribution', fontweight='bold')
    axes[0, 1].set_xlabel('Age (years)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Department Count
    dept_counts = df['Department'].value_counts()
    axes[1, 0].bar(dept_counts.index, dept_counts.values, color='mediumseagreen', edgecolor='black')
    axes[1, 0].set_title('Employees by Department', fontweight='bold')
    axes[1, 0].set_xlabel('Department')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Salary vs Experience Scatter
    axes[1, 1].scatter(df['Experience'], df['Salary'], alpha=0.6, color='purple', edgecolor='black')
    axes[1, 1].set_title('Salary vs Experience', fontweight='bold')
    axes[1, 1].set_xlabel('Experience (years)')
    axes[1, 1].set_ylabel('Salary ($)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    multi_chart_path = output_dir / "analysis_overview.png"
    plt.savefig(multi_chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Multi-chart visualization saved to {multi_chart_path}")
    
    # 2. Individual Department Chart (as in original)
    plt.figure(figsize=(8, 5))
    dept_counts.plot(kind='bar', color='steelblue', edgecolor='black')
    plt.title('Employees by Department', fontweight='bold', fontsize=14)
    plt.xlabel('Department', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    dept_chart_path = output_dir / "department_count.png"
    plt.savefig(dept_chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Department chart saved to {dept_chart_path}")
    
    # 3. Individual Salary Distribution (as in original)
    plt.figure(figsize=(8, 5))
    plt.hist(df['Salary'], bins=10, edgecolor='black', alpha=0.7, color='steelblue')
    plt.title('Salary Distribution', fontweight='bold', fontsize=14)
    plt.xlabel('Salary ($)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    salary_chart_path = output_dir / "salary_distribution.png"
    plt.savefig(salary_chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Salary distribution chart saved to {salary_chart_path}")


def save_cleaned_data(df: pd.DataFrame, output_dir: Path) -> None:
    """Save the cleaned dataset."""
    cleaned_path = output_dir / "cleaned_dataset.csv"
    df.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned dataset saved to {cleaned_path}")


def main():
    """Main execution function."""
    try:
        logger.info("=" * 60)
        logger.info("Data Cleaning & Visualization Project Started")
        logger.info("=" * 60)
        
        # Setup paths
        BASE_DIR, DATA_DIR, OUTPUT_DIR = setup_paths()
        
        # Load data
        df = load_data(DATA_DIR)
        initial_rows = len(df)
        
        # Validate data
        validate_data(df)
        
        # Analyze missing values
        missing_report = analyze_missing_values(df)
        
        # Handle missing values
        df = handle_missing_values(df)
        
        # Handle duplicates
        df = handle_duplicates(df)
        duplicate_count = initial_rows - len(df)  # Recalculate after operations
        
        # Handle outliers
        df, outlier_report, outlier_rows_removed = handle_outliers(df)
        
        # Create cleaning summary
        create_cleaning_summary(
            initial_rows=initial_rows,
            final_rows=len(df),
            duplicate_count=duplicate_count,
            outlier_rows_removed=outlier_rows_removed,
            output_dir=OUTPUT_DIR
        )
        
        # Save cleaned data
        save_cleaned_data(df, OUTPUT_DIR)
        
        # Create visualizations
        create_visualizations(df, OUTPUT_DIR)
        
        logger.info("=" * 60)
        logger.info("Data Cleaning & Visualization Project Completed Successfully")
        logger.info("=" * 60)
        logger.info(f"Final dataset shape: {df.shape}")
        logger.info(f"Outputs saved to: {OUTPUT_DIR}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()