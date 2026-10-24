from pathlib import Path

from django import forms

from .models import Document


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
}


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if not uploaded_file:
            raise forms.ValidationError(
                "Please select a file."
            )

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "This file extension is not allowed."
            )

        if uploaded_file.size > MAX_FILE_SIZE:
            raise forms.ValidationError(
                "File size must not exceed 10 MB."
            )

        return uploaded_file