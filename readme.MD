# Mastodon-ebooks

This is a simple ebooks bot for the Mastodon social media network designed to run on a Heroku free tier app. It mimics similar bots on Twitter, most notably [Tom Meagher's heroku\_ebooks](https://github.com/tommeagher/heroku_ebooks). It makes use of a number libraries, most notably [Halcy's Mastodon.py](https://github.com/halcy/Mastodon.py) to communicate with Mastodon, and [Jeremy Singer-Vine's Markovify](https://github.com/jsvine/markovify) to handle the actual toot generation.

The bot is configured to ignore all CW posts.

## Setup

You'll need a few things to set this up, most notably you'll need to be comfortable working on the command line, as well as have Git and the Heroku CLI tool installed and logged in to your account.

1. Clone this repository to a directory on your local machine.
`git clone https://github.com/srol/mastodon-ebooks.git`

2. Create a Mastodon account for your new ebooks bot. Make sure you're doing this on a bot-friendly instance. I use [botsin.space](http://botsin.space)

3. Use your new account to follow the account you want the bot to mimic. Make sure it's the only account you're following (some instances like botsin.space automatically have new accounts follow the admin.)

4. Create a new heroku app in the directory you've cloned the git repository too.
`heroku create`

5. Add the scheduler, redis-to-go and postgresql add-ons to the new Heroku app you created.
`heroku addons:create scheduler`
`heroku addons:create redistogo`
`heroku addons:create heroku-postgresql:hobby-dev`

6. Deploy the app to Heroku.
`git push heroku master`

7. Generate your Mastodon credentials.
[Mastodon.Py](https://github.com/halcy/Mastodon.py) provides instructions for how to do this in the command line, so if you feel comfortable with that, go for it. Otherwise, go back to the account you created for the bot, log in and click "settings". From here go to the "Development" tab and click "New Application". Give the bot a descriptive name, like "ebooksbot" and make sure all the scopes are checked, then click "submit." Now you should see the app you just created under Your Applications. Click on it and your credentials will be there.

8. Add your credentials to your Heroku app. There are three you need to copy over from the tab in the last instruction, and you can do this via the command line. Make sure no apostrophes, spaces or new lines are being copied over, just the tokens themselves.
`heroku config:set client_id=CLIENT_ID_FROM_MASTODON_SETTINGS`
`heroku config:set client_secret=CLIENT_SECRET_FROM_MASTODON_SETTINGS`
`heroku config:set access_token=ACCESS_TOKEN_FROM_MASTODON_SETTINGS`
You also need to add the base url of the instance you'll be using. Make sure the url is https!
`heroku config:set instance=https://YOURINSTANCEURL.HERE`

9. Provision the Heroku worker that's going to take care of most of the bot's tasks
`heroku ps:scale worker=1`

10. Run the bot for the first time. This may take a few minutes, since it's going to scrape all of your account's toots that are accessible through the API.
`heroku run python ebooks.py`
The bot should toot "hello world" when it's done.

11. Open the scheduler and set up the bot to toot automatically.
`heroku addons:open scheduler`
this will open a browser window. Click "add new job" and in the prompt with a $ sign, add
`python ebooks.py`
Set the frequency to hourly. This doesn't mean it will toot every hour, just that it has a 1-in-4 chance of tooting every hour.

12. That's it!

## Updating corpus

If you set up the book on an older version, your corpus might have picked up mentions, boosts and private posts, as well as cluttered entities like urls. The new version is updated to not do that, so if you're updating, here's how you get a fresh start.

1. Pull the newest version from Github.
`git pull`

2. Push the update to Heroku:
`git push heroku master`

3. run the corpus regeneration script. This will discord all the toots the bot has currently saved and re-save them following the new rules.
`heroku run python regenerate.py`

You can find me on Mastodon [@srol@mellified.men](http://mellified.men/@srol)
