Sigma/LUT-SQPO
========

### Warning
This project wasn't finished. It *will* run, but some features weren't implemented.

### Description
A team project for Software Quality, Processes and Organizations course at LUT university. The purpose of the service is to allow organizations and students looking for employees and jobs respectively, find each other. The service allows students to highlight their programming experience by uploading their projects and tagging relevant skills. Organizations would then search for employees via required technologies and invite suitable candidates for an interview.

### Sidenotes
One of the requirements set for the project was to utilize CKAN as data storage. This decision led to some interesting design choices since not all data could be saved there due to its technical limitations. So, some of the data including user accounts was stored in more traditional database: SQLite. Further down the line, it would have been replaced by PostgreSQL, but the project never reached its first release.

Worth noting that before the project, both developers didn't have any experience with Django. If I were to rewrite this project from scratch now, I would've used class-based views, created fewer apps, utilized django's forms capabilities and messaging system.

Since this project was developed in accordance with UPEDU process (which is a simplified version of Rational Unified Process), it is extensively documented. Documentation can be found in /docs directory.

This project was EOL'd in November '15.

### Prerequisites
- Python 3.x
- Django
- CKAN
- ckanapi (python)
- Bootstrap

### How to use
Run migrations:

    ./manage.py makemigrations
    ./manage.py migrate

And then run however you like, for example using django's dev server:

    ./manage.py runserver

### Team
- Imtiaz Ahmed (Project Manager)
- Kuchimanchi Lakshmi Prasanna (Requirements Analyst)
- Joonas Maksimainen (Software Architect)
- Eduard Telezhnikov (Front-end & Django)
- Vitezslav Kriz (Back-end and CKAN integration)
- Juho Juvani (Testing)