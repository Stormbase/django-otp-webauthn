.. _`style-guide`:

Style guide
===========

This documentation follows the `Google Developer Documentation Style Guide <https://developers.google.com/style>`_.

Apart from the style guide, here are some additional guidelines to follow when writing documentation for Django OTP WebAuthn:

Spelling
--------

Use American English spelling. For example:

* color, not colour

* optimize, not optimise

* canceled, not cancelled

Words to avoid
--------------

Avoid informal, unclear words, and internet slangs. Use the following table for guidance:

+----------+----------------+---------------------+
| Word     | Meaning        | Use instead         |
+==========+================+=====================+
| ain’t    | is not         | isn’t               |
+----------+----------------+---------------------+
| gonna    | going to       | going to            |
+----------+----------------+---------------------+
| gotta    | got to         | have to             |
+----------+----------------+---------------------+
| how’d    | how did /      | how did / how would |
|          | how would      |                     |
+----------+----------------+---------------------+
| how’ll   | how will       | how will            |
+----------+----------------+---------------------+
| I’d      | I would        | I would             |
+----------+----------------+---------------------+
| may’ve   | may have       | may have            |
+----------+----------------+---------------------+
| mayn’t   | may not        | may not             |
+----------+----------------+---------------------+
| might’ve | might have     | might have          |
+----------+----------------+---------------------+
| mightn’t | might not      | might not           |
+----------+----------------+---------------------+
| ’twas    | it was         | it was              |
+----------+----------------+---------------------+
| wanna    | want to        | want to             |
+----------+----------------+---------------------+
| YMMV     | Your mileage   | Your mileage may    |
|          | may vary       | vary                |
+----------+----------------+---------------------+
| u need to| you need to    | you need to         |
| download | download       | download            |
| Python   | Python         | Python              |
+----------+----------------+---------------------+

Commonly misused words and preferred alternatives
-------------------------------------------------

The following table shows the commonly misused words and their preferred alternatives:

+----------------+---------------------------------------------------------+
| Avoid          | Use instead                                             |
+================+=========================================================+
| cons           | disadvantages                                           |
+----------------+---------------------------------------------------------+
| desire, desired|  want or need                                           |
+----------------+---------------------------------------------------------+
| does not yet   | doesn’t                                                 |
+----------------+---------------------------------------------------------+
| enable         | Be precise by using **turn on** for features or         |
|                | **lets you** for capabilities                           |
+----------------+---------------------------------------------------------+
| pros           | advantages                                              |
+----------------+---------------------------------------------------------+
| leverage       | use **build on**, **use**, or **take advantage of**     |
|                | if needed                                               +
+----------------+---------------------------------------------------------+

Latin phrases and abbreviations
-------------------------------

Avoid Latin phrases like *ergo* or *de facto* and abbreviations like *i.e.* or *e.g.* Use clear, common English phrases instead. If possible, find a simpler way to express the idea. The only exception is *etc.*, which is acceptable when space is limited:

+------------+-----------------------+
| Avoid      | Use  instead          |
+============+=======================+
| e.g.       | for example, such as  |
+------------+-----------------------+
| i.e.       | that is               |
+------------+-----------------------+
| viz.       | namely                |
+------------+-----------------------+
| ergo       | therefore             |
+------------+-----------------------+

.. _`lists`:

Lists
-----

You can use lists to organize information in the documentation. There are two types of list:

Numbered lists
~~~~~~~~~~~~~~

Use numbered lists for step-by-step instructions when order matters. For example:

1. Install the necessary software.

2. Configure the settings.

3. Run the application.

Unnumbered lists
~~~~~~~~~~~~~~~~

Use bullet lists for items that do not follow a specific order. For example:

* Features included in the latest update

* Supported file formats

* Common error messages

Avoid overly complex nesting in lists. If a list becomes too deep, consider breaking it into smaller sections. Ensure all items in a list follow the same grammatical structure to maintain clarity.
