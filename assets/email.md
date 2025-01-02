Hello 👋,  
{% if body_response %}
We identified one question in the body of your email. The response is as follows:  

{{ body_response }}

{% if similarity_score is not none %}
Based on our knowledge base, we found relevant information with {{ "%.1f"|format(similarity_score * 100) }}% similarity to your question.
{% else %}
Note: We couldn't find any directly relevant information in our knowledge base for this question. The response is based on general knowledge.
{% endif %}
{% else %}
We could not identify any technical questions in your email body.
{% endif %}
{% if num_attachments > 1 %}
We found {{ num_attachments }} attachments in your email.
Performance summary as follows:  

- Successfully processed files: {{ num_processed_files }}
- Failed to process files: {{ num_failed_files }}
- Skipped (non-Excel) files: {{ num_skipped_files }}
Detailed summary as follows:  
{{ detailed_summary }}
{% elif num_attachments == 1 %}
We processed your Excel file with the following results:  
{{ detailed_summary }}
Please find the report in the attachment.
{% elif num_attachments == 0 %}
We did not find any Excel files in your email.
{% endif %}

Best regards,  
DeepBridge
