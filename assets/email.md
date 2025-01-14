Hello 👋,  

{%- if body_response %}
    {%- if "don't have enough relevant information" in body_response %}

{{ body_response }}
    {%- else %}

{{ "We identified one question in the body of your email. **The response is as follows:**" | safe }}  

{{ body_response }}

        {%- if similarity_score is not none %}
        
{{ "Based on our knowledge base, we found relevant information with a **cosine similarity score of " ~ "%.2f"|format(similarity_score) ~ "**. Cosine similarity ranges from -1 to 1, where 1 means identical semantic meaning, 0 means unrelated, and scores above 0.7 typically indicate strong semantic similarity." | safe }}

            {%- if document_url %}
{{ "You can find more information in the source document [here](" ~ document_url ~ ")." | safe }}
            {%- endif %}
        {%- endif %}
    {%- endif %}
{%- else %}

We could not identify any technical questions in your email body.
{%- endif %}

{%- if num_attachments > 1 %}

We found {{ num_attachments }} attachments in your email.
Performance summary as follows:  

- Successfully processed files: {{ num_processed_files }}
- Failed to process files: {{ num_failed_files }}
- Skipped (non-Excel) files: {{ num_skipped_files }}

Detailed summary as follows:

{{ detailed_summary }}
{%- elif num_attachments == 1 %}
We processed your Excel file with the following results:  
{{ detailed_summary }}
Please find the report in the attachment.
{%- elif num_attachments == 0 %}

We did not find any Excel files in your email.
{%- endif %}

Best regards,  
DeepBridge
