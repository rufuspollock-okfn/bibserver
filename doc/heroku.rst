.. _heroku:

=================
Running on heroku
=================

Create a heroku account - see http://heroku.com

Install heroku - see https://toolbelt.heroku.com

    wget -qO- https://toolbelt.heroku.com/install.sh | sh


Login to heroku and follow option to upload public key if desired

    heroku login


Get into a copy of the bibserver code

    git clone git://github.com/okfn/bibserver.git
    cd bibserver


Create and rename the heroku app

    heroku create
    heroku rename bibsoup
    
    
Add the elasticsearch addon. 
Addons require account verification, which requires a credit card but no charges are taken.

    heroku addons:add bonsai


For running on heroku, you will need to customise the config.json file directly. 
Set "debug": false and set the ELASTICSEARCH_HOST and DB as well. 
Once you have added the bonsai addon, you will find these details on your app dashboard on heroku.com. 

Manually push the mappings to the elasticsearch index created from the bonsai addon. 
You can find the mappings in config.json. Do the /record/_mapping and the /collection/_mapping.

    curl -X PUT 'BONSAI_ADDRESS/record/_mapping' -d 'MAPPING'


Then update the repo and push the changes to heroku

    git add .
    git commit -am 'USEFUL MESSAGE HERE'
    git push heroku master


Now it should be ready to run

    heroku ps:scale web=1


Check your heroku dashboard for your app, and view it to see if it is running. 
Then customise URLs and so on as required.


