def student_payload(form):
    return {
        "student_code": form.get("student_code", "").strip(),
        "name": form.get("name", "").strip(),
        "gender": form.get("gender", "").strip(),
        "age": form.get("age"),
        "phone": form.get("phone", "").strip(),
        "address": form.get("address", "").strip(),
        "guardian_name": form.get("guardian_name", "").strip(),
        "guardian_phone": form.get("guardian_phone", "").strip(),
        "emergency_phone": form.get("emergency_phone", "").strip(),
        "photo_url": form.get("photo_url", "").strip(),
        "class_id": form.get("class_id") or None,
    }


def validate_student(data):
    errors = []
    if not data["student_code"]:
        errors.append("សូមបញ្ចូលលេខកូដសិស្ស។")
    if not data["name"]:
        errors.append("សូមបញ្ចូលឈ្មោះសិស្ស។")
    if data["gender"] not in ("Male", "Female", "Other"):
        errors.append("សូមជ្រើសរើសភេទឱ្យបានត្រឹមត្រូវ។")
    try:
        data["age"] = int(data["age"])
        if data["age"] <= 0:
            errors.append("អាយុត្រូវតែធំជាង ០។")
    except (TypeError, ValueError):
        errors.append("អាយុត្រូវតែជាលេខ។")
    return errors
