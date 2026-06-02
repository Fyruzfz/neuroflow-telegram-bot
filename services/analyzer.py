"""
NeuroFlow AI Bot - Data Analysis Service
Uses pandas + Ollama for insights
"""

import os
import subprocess
import sys
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")


async def run_analysis(filepath: str) -> dict:
    """
    Analyze a CSV/Excel file and return summary.
    Returns {"success": bool, "summary": str, "report_path": str, "error": str}
    """
    try:
        import pandas as pd

        # Load data
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        if df.empty:
            return {"success": False, "error": "File is empty."}

        rows, cols = df.shape

        # Build summary
        summary_parts = [
            f"*Data Analysis Report*",
            f"",
            f"*File:* {os.path.basename(filepath)}",
            f"*Rows:* {rows:,} | *Columns:* {cols}",
            f"",
            f"*Column Overview:*",
        ]

        for col in df.columns:
            dtype = str(df[col].dtype)
            nulls = df[col].isnull().sum()
            null_pct = (nulls / rows) * 100 if rows > 0 else 0

            if pd.api.types.is_numeric_dtype(df[col]):
                stats = f"min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}"
            else:
                unique = df[col].nunique()
                stats = f"{unique} unique values"

            summary_parts.append(f"- *{col}* ({dtype}): {stats}, {null_pct:.0f}% missing")

        # Top rows preview
        summary_parts.append("")
        summary_parts.append("*Preview (first 5 rows):*")
        preview = df.head(5).to_string(index=False)
        summary_parts.append(f"```\n{preview[:500]}\n```")

        # Correlations for numeric columns
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) >= 2:
            corr = df[num_cols].corr()
            summary_parts.append("")
            summary_parts.append("*Top Correlations:*")
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    val = corr.iloc[i, j]
                    if abs(val) > 0.3:
                        summary_parts.append(f"  {num_cols[i]} vs {num_cols[j]}: {val:.3f}")

        summary = "\n".join(summary_parts)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"report_{timestamp}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(summary)

        return {"success": True, "summary": summary, "report_path": report_path}

    except ImportError:
        return {"success": False, "error": "pandas not installed. Run: uv pip install pandas openpyxl"}
    except Exception as e:
        # Fallback: basic Python analysis
        return await _fallback_analysis(filepath)


async def _fallback_analysis(filepath: str) -> dict:
    """Basic analysis without pandas."""
    import csv

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows_list = list(reader)

        if not rows_list:
            return {"success": False, "error": "File is empty."}

        headers = rows_list[0]
        data = rows_list[1:]
        total_rows = len(data)

        summary_parts = [
            f"*Basic Data Analysis*",
            f"",
            f"*File:* {os.path.basename(filepath)}",
            f"*Rows:* {total_rows:,} | *Columns:* {len(headers)}",
            f"",
            f"*Columns:* {', '.join(headers[:10])}",
            f"",
            f"*First 5 rows:*",
        ]

        for row in data[:5]:
            summary_parts.append(f"  {', '.join(row[:5])}")

        summary = "\n".join(summary_parts)
        return {"success": True, "summary": summary}

    except Exception as e:
        return {"success": False, "error": f"Analysis error: {str(e)[:300]}"}
