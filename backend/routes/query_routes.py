from flask import Blueprint, request, jsonify
from backend.email_service import send_email
from backend.services.llm_service import generate_sql_from_llm, fix_sql_with_llm, optimize_sql_with_llm, explain_result_with_llm
from backend.services.sql_service import run_query
# from backend.utils.sql_validator import is_safe_query
from backend.utils.schema_manager import refresh_schema
# from backend.services.query_validator import validate_query_with_llm
from backend.services.insight_service import generate_insights
from backend.services.visualization_service import generate_chart_config
from backend.utils.schema_manager import get_schema_graph
from backend.services.report_service import generate_report
from backend.services.insight_service import generate_insights
from backend.services.sandbox_manager import create_sandbox_db
from backend.db import set_db_urls, get_sandbox_db_url, get_prod_db_url
from backend.extensions import init_prod_db, init_sandbox_db

query_bp = Blueprint("query", __name__)

@query_bp.route("/query", methods=["POST"])
def generate_query():
    data = request.get_json()
    optimize = data.get("optimize", False)
    user_query = data.get("query")
    provider = data.get("provider", "groq")
    explain = data.get("explain", False)
    visualize = data.get("visualize", False)

    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    try:
        # validation = validate_query_with_llm(user_query, provider)

        # if validation != "YES":
        #     return jsonify({
        #         "error": "Query cannot be answered with current database schema.",
        #         "validation": validation
        #     }), 400

        sql = generate_sql_from_llm(user_query, provider)
        sql = generate_sql_from_llm(user_query, provider)

        send_email(
            "✅ AutoQuery Success",
            f"""
User Input:
{user_query}

Generated SQL:
{sql}

Status: SUCCESS
"""
        )

        final_sql = sql

        if optimize:
            optimized_sql = optimize_sql_with_llm(sql, provider)

            # if is_safe_query(optimized_sql):
            #     final_sql = optimized_sql
            # else:
            #     optimized_sql = None
        else:
            optimized_sql = None

        # if not is_safe_query(sql):
        #     return jsonify({
        #     "error": "Unsafe query detected!",
        #     "sql": sql
        # }), 400

        raw_data = run_query(sql)

        if raw_data["type"] == "select":
            db_rows = raw_data["data"]
        else:
            db_rows = []

        db_result = {
            "success": True,
            "data": db_rows,
            "error": None
        }

        chart = None

        # Safe chart generation
        if visualize and db_result["success"] and db_result["data"]:
            chart = generate_chart_config(
                db_result["data"][:10],  # now db_result["data"] is a list
                user_query,
                provider
            )

        if not isinstance(chart, dict) or "datasets" not in chart:
            chart = None

        explanation = None
        if explain and db_result["success"]:
            explanation = explain_result_with_llm(
                user_query,
                final_sql,
                db_result["data"],
                provider
            )

        return jsonify({
            "original_sql": sql,
            "optimized_sql": optimized_sql,
            "executed_sql": final_sql,
            "data": db_result["data"],
            "explanation": explanation,
            "chart": chart,
            "provider_used": provider,
            "auto_fixed": False
        })

    except Exception as e:

        print("SQL Failed, attempting fix...")

        return jsonify({"error": str(e)}), 500
    

@query_bp.route("/connect-db", methods=["POST"])
def connect_db():

    data = request.get_json()
    db_url = data.get("database_url")

    if not db_url:
        return jsonify({"error": "Database URL required"}), 400

    try:
        init_prod_db(db_url)
        refresh_schema()

        sandbox_name = "sandbox_db"
        create_sandbox_db(db_url, sandbox_name)

        sandbox_url = db_url.replace(
            db_url.split("/")[-1],
            "sandbox_db"
        )

        set_db_urls(db_url, sandbox_url)

        return jsonify({
            "message": "Database connected & sandbox ready"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# @query_bp.route("/insights", methods=["POST"])
# def get_insights():
#     data = request.get_json()
#     provider = data.get("provider", "groq")

#     try:
#         insights = generate_insights(provider)

#         return jsonify({
#             "insights": insights,
#             "provider_used": provider
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@query_bp.route("/insights", methods=["POST"])
def get_insights():
    data = request.get_json()
    print("DATA IN INSIGHTS: ",data)

    provider = data.get("provider", "groq")
    report_data = data.get("data")

    print("Report data: ",report_data)

    try:
        insights = generate_insights(report_data, provider)

        return jsonify({
            "insights": insights,
            "provider_used": provider
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@query_bp.route("/schema-graph", methods=["GET"])
def schema_graph():
    try:
        graph = get_schema_graph()
        return jsonify(graph)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@query_bp.route("/report", methods=["POST"])
def generate_report_api():

    data = request.get_json()
    user_query = data.get("query")
    provider = data.get("provider", "groq")

    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    try:
        report = generate_report(user_query, provider)

        insights = generate_insights(report, provider)

        return jsonify({
            "report": report,
            "insights": insights
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@query_bp.route("/reset-sandbox", methods=["POST"])
def reset_sandbox():

    try:
        db_url = get_prod_db_url()

        if not db_url:
            return jsonify({"error": "No DB connected yet"}), 400

        create_sandbox_db(db_url)

        return jsonify({
            "message": "Sandbox reset successfully"
        })

    except Exception as e:
        send_email(
            "❌ AutoQuery Failed",
            f"""
Error:
{str(e)}

Status: FAILED
"""
        )

        print("Sandbox reset failed...")

        return jsonify({"error": str(e)}), 500