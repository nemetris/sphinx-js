{{ name | escape | underline }}

.. js:automodule:: {{ name }}
{% if members_option %}
    :members: {{ members }}
{% endif %}
{% if exclude_members %}
    :exclude-members: {{ exclude_members }}
{% endif %}
{% if is_private %}
    :private-members:
{% endif %}
