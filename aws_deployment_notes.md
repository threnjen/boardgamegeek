# Notes and checklist for AWS deployment

- Create ECR Registry for this repo
- Set up user role for GitHub actions, create export keys
- Add GitHub deployment action to this repo
- Confirm repo pushes up to AWS
- lambda trigger needs to read URLs json, parse groups, launch ECS on a per-group basis
- Load up to AWS - boardgames_ranks.csv

## Preparing code for AWS

- Rewrite code for AWS work - modularize as much as possible
- Consider breaking this repo into discrete projects that handle different things. E.G. Scraping vs cleaning
- Convert notebooks into proper scripts. Figure out if I separate different areas into different ECR images, or use all one ECR image and use pass-in vars to decide on proper behavior
