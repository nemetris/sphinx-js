{{ name | escape | underline }}

.. js:automodule:: {{ name }}
{% if members %}
    :members:
{% endif %}
{% if exclude_members %}
    :exclude-members: {{ exclude_members }}
{% endif %}
{% if private_members %}
    :private-members:
{% endif %}
