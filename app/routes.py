"""
Routes and API endpoints for Notefy application
"""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file
from app import db
from app.models import Note
from sqlalchemy import text
import json
import io
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@main_bp.route("/health")
def health():
    """Health check endpoint for Kubernetes probes"""
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "connected"
        status_code = 200
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "disconnected"
        status_code = 503

    return jsonify({"status": "UP" if status_code == 200 else "DOWN", "database": db_status}), status_code


@main_bp.route("/api/notes", methods=["GET"])
def get_notes():
    """Get all notes"""
    try:
        notes = Note.query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
        return jsonify({"success": True, "notes": [note.to_dict() for note in notes], "count": len(notes)})
    except Exception as e:
        logger.error(f"Error fetching notes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/notes/<int:note_id>", methods=["GET"])
def get_note(note_id):
    """Get a specific note"""
    note = Note.query.get_or_404(note_id)
    return jsonify({"success": True, "note": note.to_dict()})


@main_bp.route("/api/notes", methods=["POST"])
def create_note():
    """Create a new note"""
    try:
        data = request.get_json()

        if not data or not data.get("title") or not data.get("content"):
            return jsonify({"success": False, "error": "Title and content are required"}), 400

        note = Note(
            title=data["title"],
            content=data["content"],
            tags=",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags", ""),
            color=data.get("color", "default"),
            is_pinned=data.get("is_pinned", False),
        )

        db.session.add(note)
        db.session.commit()

        logger.info(f"Note created: {note.id}")

        return jsonify({"success": True, "note": note.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating note: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    """Update an existing note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.get_json()

        if "title" in data:
            note.title = data["title"]
        if "content" in data:
            note.content = data["content"]
        if "tags" in data:
            note.tags = ",".join(data["tags"]) if isinstance(data["tags"], list) else data["tags"]
        if "color" in data:
            note.color = data["color"]
        if "is_pinned" in data:
            note.is_pinned = data["is_pinned"]

        db.session.commit()

        logger.info(f"Note updated: {note.id}")

        return jsonify({"success": True, "note": note.to_dict()})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating note: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    """Delete a note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()

        logger.info(f"Note deleted: {note_id}")

        return jsonify({"success": True, "message": "Note deleted successfully"})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting note: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/search", methods=["GET"])
def search_notes():
    """Search notes with SQL injection vulnerability"""
    try:
        query = request.args.get("q", "")

        if not query:
            return jsonify({"success": True, "notes": [], "count": 0})

        # Fixed E501 by splitting the string
        sql = (f"SELECT * FROM notes WHERE content LIKE '%{query}%' OR title LIKE '%{query}%' "
               f"OR tags LIKE '%{query}%' ORDER BY updated_at DESC")
        result = db.session.execute(text(sql))

        notes = []
        for row in result:
            notes.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "content": row.content,
                    "tags": row.tags.split(",") if row.tags else [],
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                    "is_pinned": row.is_pinned,
                    "color": row.color,
                }
            )

        return jsonify({"success": True, "notes": notes, "count": len(notes), "query": query})

    except Exception as e:
        logger.error(f"Error searching notes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/export/json", methods=["GET"])
def export_json():
    """Export all notes as JSON"""
    try:
        notes = Note.query.order_by(Note.created_at.desc()).all()
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_notes": len(notes),
            "notes": [note.to_dict() for note in notes],
        }

        output = io.BytesIO()
        output.write(json.dumps(export_data, indent=2).encode("utf-8"))
        output.seek(0)

        return send_file(output, mimetype="application/json", as_attachment=True, download_name="notefy_export.json")

    except Exception as e:
        logger.error(f"Error exporting notes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/export/markdown", methods=["GET"])
def export_markdown():
    """Export all notes as Markdown"""
    try:
        notes = Note.query.order_by(Note.created_at.desc()).all()

        markdown_content = f"""# Notefy Export
        
Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Total Notes: {len(notes)}

---

"""

        for note in notes:
            markdown_content += note.to_markdown() + "\n\n"

        output = io.BytesIO()
        output.write(markdown_content.encode("utf-8"))
        output.seek(0)

        return send_file(output, mimetype="text/markdown", as_attachment=True, download_name="notefy_export.md")

    except Exception as e:
        logger.error(f"Error exporting markdown: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route("/api/stats", methods=["GET"])
def get_stats():
    """Get application statistics"""
    try:
        total_notes = Note.query.count()
        pinned_notes = Note.query.filter_by(is_pinned=True).count()

        all_tags = []
        notes_with_tags = Note.query.filter(Note.tags != "").all()
        for note in notes_with_tags:
            all_tags.extend([tag.strip() for tag in note.tags.split(",") if tag.strip()])

        from collections import Counter

        tag_counts = Counter(all_tags)
        popular_tags = [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(10)]

        return jsonify(
            {
                "success": True,
                "stats": {"total_notes": total_notes, "pinned_notes": pinned_notes, "popular_tags": popular_tags},
            }
        )

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500