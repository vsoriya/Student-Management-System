def validate_register_form(form):
    errors = []
    if not form.get("name", "").strip():
        errors.append("សូមបញ្ចូលឈ្មោះ។")
    if not form.get("email", "").strip():
        errors.append("សូមបញ្ចូលអ៊ីមែល។")
    if len(form.get("password", "")) < 6:
        errors.append("ពាក្យសម្ងាត់ត្រូវមានយ៉ាងហោចណាស់ ៦ តួអក្សរ។")
    return errors
