# Fix the frontend bug with reacting to own comment

- STATUS: CLOSED
- PRIORITY: 70
- TAGS: UI, bug, comments, reactions

Currently, when a user tries to like/dislike their own comment, they get a 400 Bad Request response. The frontend does not properly handle that and shows `undefined` as the number of likes and dislikes on the comment.
