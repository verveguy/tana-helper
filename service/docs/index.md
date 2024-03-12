# 🤝 Tana Helper
## Overview & Installation
One of the great things about Tana is that it is able to call external systems via the <code>Make API request </code>command. Not only can it make calls to internet services with APIs to fetch data into Tana, you can also pass existing Tana node data to these APIs and then receive results in return. The results of these calls can be added as new Tana nodes or can be used as input to further features like the built-in AI integration.

In my own daily use of Tana I have found myself wanting various enhancements to Tana - things that aren\'t built-in already. The <code>Make API request</code> command gives me the ability to call out to custom code. Importantly, that code doesn\'t have to run "on the internet" somewhere but can in fact run on my local laptop via the <code>Avoid Proxy</code> setting of <code>Make API request</code>. As a software engineer, this really opens things up for me. 
  - And so I built a small service called `tana-helper` and started adding functions to it.
GitHub - verveguy/tana-helper - Small web service to handle API calls from Tana and do useful things
  URL:: https://github.com/verveguy/tana-helper/
  Site name:: GitHub
<code>tana-helper</code> is [[open source^vNQsr85-X1mQ]], licensed under the MIT license, and is completely free.
Installation
  If you use a Mac the simplest way to get<code> tana-helper</code> running on your laptop is to [[download^foQuyw-yK7Pb]]the double-clickable <code>[[Tana Helper.app^nb2Es9zeCTov]]</code>. This should work on any Mac running Mac OSX 12 (Monterey) or newer with either Intel or Apple Silicon. Open the .dmg and drag the Tana Helper app to your Applications folder.
  For Windows users, there\'s now also a Windows executable packaged as a tar.gz file.  See  [[Releases Â· verveguy/tana-helper^GirYz_SmIbhA]]You\'ll need to unpack the tarball which will create a folder. Put this anywhere you like.
  If you are a developer and want to play with the code, you can get the <code>tana-helper</code> service running on your laptop by following the instructions at: [[GitHub - verveguy/tana-helper: Small web service to handle API calls from Tana and do useful things^IENu5mWV7Q3n]]. (follow README instructions. â\x9a\xa0ï¸\x8f Needs developer knowledge).
Running
  For Mac users, just double-click the Tana Helper app. This will add a menu bar helper icon with a very simple menu. Starting <code>tana-helper</code> from the menu should launch a Terminal window showing you the log as Tana Helper runs and handles requests.
  For Windows users, you can either launch the <code>tanahelper.exe</code> which will give you a small menu tray app which you can right-click to get the action menu. Or you can double-click the <code>start.exe</code> which should just launch a terminal window showing the log as <code>tana-helper</code> runs.
# Background
## Calendar integration
    I spend most of my day on zoom talking to various people about a lot of topics, including projects and technology. So most of my workflow in Tana revolves around meetings. Not surprisingly, the first example of something I really _really_ wanted was fetching my Outlook calendar and making a series of <code>#meeting</code> nodes in Tana, pre-populated with the names of the people I was meeting with. I was able to write the code for this (originally in Swift) and then call it from Tana. That code is now included here in <code>tana-helper</code>. (See [[ð\x9f\x93\x86  Import Calendar into Tana (Mac only)^JnWAWvvncFF7]])
## Building up knowledge
    As I take notes in these many meetings, I often create inline references to <code>#topic</code> nodes. Topics might be projects, technologies, events, etc. Each of these probably exists in my library, created at some earlier time. So meetings are one of the main ways I accumulate more knowledge about these topics. Most meetings also touch on more than one topic, and also have extraneous notes in them as well. So I can\'t just organize each meeting neatly under a topic. After using Tana for a while, I found that I wanted to copy those notes _to the Library nodes themselves_ rather than have them only appear in my meeting notes. Over time, this let me build up more and more knowledge of a topic through many conversations with my <code>#topic</code> nodes accumulating all that knowledge. _(See_ [[ð\x9f\x93\x8c Harvesting inline references^Eb8g90_U2G]]_)_.
    People have asked me why the "References" section at the bottom of a node panel isn\'t sufficient - why did I want the actual content moved to the node? Initially it was a UI thing: the references section is way down the bottom of the panel. But the more important reason now is that I really want a topic node to contain the accumulated content _so that I can embed the whole node it in a vector database with all of the relevant content included._
    This is because, as I build up these <code>#topic</code> nodes, I want to query many of these same topics by semantic content rather than just text matching. I want to find topics that are similar or related in ways that perhaps aren\'t initially obvious. Since Tana can\'t do that (yet), I was able to write some code to copy the nodes to an external vector database as "embeddings" computed by OpenAI which I could then search by "semantic proximity" to any question I might want to ask of my own notes. Two Tana <code>Make API </code>commands are then all it takes - one to upsert a topic node into the database, and one to query the database using my current node as the "similarity" query. The vector database I originally chose was Pinecone, but a better choice now is ChromaDB, which stores all the data locally. (I now support Weaviate as well.) _(See_ [[â\x86\x96ï¸\x8f Using Vector databases with Tana^D3KI2-RZM3qG]]_)_
  Integrating with things
    A lot of working with Make API commands is dealing with JSON and Tana Paste. Unfortunately, Tana doesn\'t yet have automated conversion between these formats and so I added helper functions to do that as well. Inspired by my own needs and the needs of other folks in the Tana community, I added  [[ð\x9f\x94\xa0 Functions for JSON / Tana Paste bi-directional conversion^LLliYxGNev]]and [[ð\x9f\x9aª Tana Helper as JSON proxy gateway^V0kXXnYRfj]].  The Tana Paste to JSON conversion also allows for a "CSV export" in case you want to dump tables of data from Tana in CSV format.
  Pushing data into Tana
    An interesting diversion has been working out how to push data into Tana from the outside world. Make API is great, but you have to initiate those calls from within the Tana UI. I also want to be able to push data into Tana, even when it\'s not running. Thankfully the Tana Input API came along which gives us the first step. Sadly, it doesn\'t support Tana paste, and thus requires a lot of a priori hard-coded knowledge (e.g. tag node ids and field schemas) to be effective for more than simple text nodes. In order to ease the burden a little, I built [[ð\x9fª\x9d Automagic Webhooks for Tana Input API^KJQMq0qe1D]]and more recently, the Tana Paste Input Queue features.
  Tana Functions
    I think someone asked a question in the Tana slack community about whether Tana might have functions in the future.Since most of tana-helper is written in python, and many of the functions are relatively short, I decided I\'d try and have code _written in Tana_ passed to tana-helper on the fly. The result is covered below in  [[ð\x9f\x90\x8d Running user-defined python^l7dQ2eDwJK]].
  Visualization
    And then, truly "just for the sake of it", I built the [[ð\x9f\x8c\x83 Tana Visualizer^tsakXNgmUF]]. It\'s a small webapp included in <code>tana-helper</code> that lets you do things like this with a JSON export of your Tana workspace:
    ![Interactive 3D visualization of my Tana knowledge graph](https://firebasestorage.googleapis.com/v0/b/tagr-prod.appspot.com/o/notespace%2Fbpjadam%40gmail.com%2Fuploads%2F2023-11-25T04%3A35%3A35.631Z-CleanShot%202023-11-24%20at%2023.35.29.png?alt=media&token=4057c8fc-35a8-4c5f-8eb3-5312bd2fcd25) 
      Recording: [[CleanShot 2023-06-08 at 22.13.31^cqNhPRTCNUN1]]
  So in summary,<code>[[tana-helper^suaygeUMX-ek]]</code> does a bunch of useful stuff, all made possible by the built-in Tana <code>Make API request</code> command. Each command calls a different API \'endpoint\' of <code>tana-helper;</code> you can think of it as a kind of "swiss army knife" of services.
Tana configuration
  Once you have the <code>tana-helper</code> service running, you\'ll need a set of Tana Command nodes to call it. The best thing to do is [[load this content with all of the commands as a Tana template^NkyOdUCPW_OM]].
  Once you\'ve done that, you will need to configure a few secrets  - as you try to use each command, Tana will prompt you. If you want to use the AI related features (including vector databases), you need to have an OpenAI key and have turned on _Tana Labs --> AI For Builders_ in your Tana settings.
  To make it easier to setup your <code>tana-helper</code> base URL, I\'ve used the Tana support for secrets. The first time you run one of these commands in Tana, you\'ll be prompted to fill in the value for the HelperURL. If you are running locally, use <a href="http://localhost:8000">http://localhost:8000</a> (or whatever port you\'re running on if you\'ve tweaked the build). For server deployments of <code>tana-helper</code>, configure appropriately (some help is in the README on github).
Features
  ð\x9f\x93\x86  Import Calendar into Tana (Mac only)
    This feature allows you to pull your calendar into Tana via the Apple Calendar API. It uses your Apple Calendar configuration to act as a "gateway" to your calendar services. This allows it to reach iCloud, Google and Office365 calendars.
    The <code>/calendar</code> endpoint will by default return you a list of your meetings for today from a calendar named "Calendar".
    You can change things with the following JSON payload. All fields are optional.
```json
{
  "me": "self name", // your own name to avoid adding you as an attendee
  "meeting": "#tag", // the tag to use for meetings defaults to #meeting
  "person": "#tag", // tag for people / attendees defaults to #person
  "solo": true | false, // include meetings with just one person (yourself?)
  "one2one": "#tag", // tag for 1 to 1 meetings, defaults to #1:1
  "calendar": "Calendar", // the name of the Calendar to read from
  "offset": -n | 0 | +n // how many days before or after today to start from
  "range": &gt;= 1 // how many days to retrieve. Defaults to 1
}
```
    Commands
      Get Today\'s Calendar
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/calendar
            Avoid using proxy:: [X] 
            API method:: POST
            Headers:: Content-Type: application/json
            Parse result:: Tana Paste
            Payload:: 
              {
                "me": "Brett Adam",
                "person": "#person",
                "calendar": "Calendar"
              }
    Usage
      Make sure the Apple Calendar app is running (you may get an error response if it isn\'t. The script will auto-launch it but sometimes the first time it hasn\'t started yet)
      cmd-K "Get Today\'s Calendar" should fetch your calendar entries for today and insert them into your Tana workspace as children of the current node.
      You can tailor the options by adjusting the _Payload_ field of the Get Today\'s Calendar command Make API node.
      Make sure you set the "calendar" property of the Payload field. Set it to the name of your calendar as it appears in the Apple Calendar app.
      The most common cause of problems is that you ask for a calendar thatÂ\xa0_does not exist_. The script defaults toÂ\xa0<code>Calendar</code>Â\xa0as the name of your calendar. You can change this by passingÂ\xa0<code>"calendar": "<your calendar name>"</code>Â\xa0in the JSON payload.
  â\x86\x96ï¸\x8f Using Vector databases with Tana
    IfÂ\xa0youâ\x80\x99reÂ\xa0interested in using a vector DB with your Tana nodes, I have three variants all working - [[Vector Database for Vector Search | Pinecone^FSeA7ZyXL07v]](hosted service), [[the AI-native open-source embedding database^le8vmnhEGroZ]](local on your machine) and [[Welcome | Weaviate - vector database^VhgXQCPdQs74]](also local).Â\xa0You also need an OpenAI account.
    What is a Vector Database?
      Basically, a vector database is like any other database in that it stores records which can later be queried.The difference is that what is stored is an â\x80\x9cembeddingâ\x80\x9d - which you can think of as a â\x80\x9cmagic numberâ\x80\x9d that somehow captures the meaning of a chunk of text.Â\xa0These embeddings are generated by OpenAI.Â\xa0You give it text, it gives you an embedding.
      OnceÂ\xa0youâ\x80\x99veÂ\xa0got a bunch of these embeddings stored in your vector database, you can then query it â\x80\x9cby exampleâ\x80\x9d.Â\xa0By this, I mean that you take some new chunk of text, get the magic embedding for it and then ask â\x80\x9cgive me all the stored embeddings that are â\x80\x98closeâ\x80\x99 to this new embeddingâ\x80\x9d.What comes back are a set of previously stored embeddings, each with some measure of â\x80\x9cdistance fromâ\x80\x9d or â\x80\x9csimilarity toâ\x80\x9d the embedding in question. And each can also have an ID or other reference back to the original source text.Â\xa0In my case, the Tana node ID.This capability is sometimes described as similarity search or semantic search.Â\xa0The idea being that these magic numbers somehow encode the meaning.
      The reasonÂ\xa0theyâ\x80\x99reÂ\xa0called vector databases is because the embedding is actually an array of numbers.Â\xa0In the case of OpenAI embeddings, 1536 numbers per embedding.Â\xa0And the math they do to figure out â\x80\x9csimilarityâ\x80\x9d is vector math.
    What can I do with one using Tana?
      Using the following Tana commands, you push your Tana Nodes into the vector DB and then query that database to get back a list of relevant nodes. They will appear as references in Tana, just like a native Tana Query does.
      So itâ\x80\x99s basically a form of â\x80\x9csemantic searchâ\x80\x9d for Tana, powered by OpenAI and your choice of vector database.
    Vector database options
      Tana ChromaDB Experiments
        What is this?
          These commands take Tana nodes (+context) and add them to the [[ChromaDB^Fa6r66jZpg2O]]vector database. This is done by first passing them to OpenAI to generate an embedding (a vector with 1536 dimensions). This vector is then inserted into Chroma with the Tana nodeId as the key.
          Chroma allows us to then query for "similar nodes", each with a "score" relative to our query. The query is also just a Tana node, converted into an embedding by OpenAI. The richer the query, the better the vector search should be in theory.
          Importantly, this is not ChatGPT-style "completions". It\'s a form of search for your own Tana content. It won\'t find (or generate) things you don\'t already know.
        Setup
          You\'ll need an OpenAI API Key to use this. You should be prompted to save this safely in your local Tana environment when you first use the commands.
        Commands: There are four Chroma commands implemented.
          Update - which stores the Tana node (with all children as context data) as an embedding in Chroma
            Update Chroma embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  URL:: ${secret:HelperURL}/chroma/upsert
                  Parse result:: Disregard (don\'t insert)
                  Headers:: Content-Type: application/json
                  Payload:: { "openai": "${secret:OpenAIKey}", "nodeId": "${sys:nodeId}", "tags": "${sys:tags}", "name": "${name}", "context": "${sys:context}"}
                  API method:: POST
          Query - which takes your current node, turns it into an embedding and then finds all semantically similar nodes in Chroma.
            Query Chroma embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  URL:: ${secret:HelperURL}/chroma/query
                  Parse result:: Tana Paste
                  Headers:: Content-Type: application/json
                  Payload:: { "openai": "${secret:OpenAIKey}", "nodeId": "${sys:nodeId}", "tags": "${sys:tags}", "score": "0.78", "context": "${sys:context}"}
                  API method:: POST
          Remove - which takes your current node and simply deletes it from Chroma.
            Remove Chroma embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  Parse result:: Disregard (don\'t insert)
                  URL:: ${secret:HelperURL}/chroma/delete
                  Payload:: 
                    {
                      "openai": "${secret:OpenAIKey}",
                      "nodeId": "${sys:nodeId}"
                    }
                  Headers:: Content-Type: application/json
                  API method:: POST
          Purge - which removes all content from your ChromaDB
            Purge Chroma
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  URL:: ${secret:HelperURL}/chroma/purge
                  Avoid using proxy:: [X] 
                  API method:: POST
        Demo topics - The following notes were generated by asking ChatGPT various questions for the purposes of building a demo research base. They were then inserted into the Chroma database using the Update Chroma embedding command. Do this yourself by cmd-K "Select Children" and then cmd-K "Update Chroma"
          William Tell is a legendary Swiss folk hero who is known for his incredible archery skills and his role in the Swiss struggle for independence. According to legend, William Tell was a skilled archer who lived in the early 14th century in the canton of Uri, Switzerland. The region was under the control of the Habsburgs, who were known for their oppressive rule and high taxes.
          One day, William Tell was approached by a Habsburg official who demanded that he shoot an apple off of his son\'s head with his bow and arrow. If he refused or missed, both he and his son would be executed. William Tell successfully shot the apple off of his son\'s head, but was arrested for carrying a concealed weapon. He was sentenced to death, but managed to escape and went on to lead a rebellion against the Habsburgs
          The story of William Tell has become a symbol of Swiss independence and resistance against tyranny. It has been retold in countless books, plays, and movies, and his image can be found on everything from coins to postage stamps.
          Archery has a long and rich history that dates back to ancient times. The earliest evidence of archery dates back to around 10,000 BC, when the first bows were made from materials such as wood, bone, and sinew. Archery was used for hunting and warfare, and it quickly became an important skill for many cultures around the world.
          In ancient Egypt, archery was used for hunting and in warfare. The Egyptians used composite bows made from layers of wood, horn, and sinew, which were highly effective in battle. In ancient Greece, archery was also used in warfare, but it was also an important sport. The Greeks held archery competitions during the Olympic Games, and archery was considered a noble pursuit.
          In medieval Europe, archery was an important part of warfare. The English longbow was a powerful weapon that could penetrate armor, and it played a key role in many battles, including the Battle of Agincourt in 1415. Archery was also an important sport in medieval Europe, and archery competitions were held throughout the continent.
          Today, archery is still a popular sport and hobby. It is also used in hunting and in some forms of warfare. Modern archery equipment has come a long way from the simple bows of ancient times, and there are now many different types of bows and arrows available for different purposes.
          Philosophy is a branch of knowledge that deals with fundamental questions about existence, reality, knowledge, values, reason, mind, and language. It seeks to understand the nature of the world and our place in it, as well as to explore the meaning and purpose of life. Philosophers use critical thinking, logic, and argumentation to analyze and evaluate different ideas and theories, and to develop their own perspectives on these issues. Some of the major areas of philosophy include metaphysics, epistemology, ethics, political philosophy, and aesthetics.
          Greek archery was an important aspect of ancient Greek warfare. The Greeks used a type of bow called the composite bow, which was made of layers of wood, horn, and sinew. These bows were powerful and could shoot arrows over long distances. Greek archers were often used as skirmishers, harassing enemy troops with arrows before the main battle. They were also used to defend fortifications and ships. The most famous Greek archers were the Cretan archers, who were known for their skill and accuracy. Archery was also an important sport in ancient Greece, with competitions held at the Olympic Games.
          Switzerland has a rich history of classical music and has produced many notable composers. Some of the most famous Swiss composers include:
            Arthur Honegger: He was a prominent composer in the early 20th century and is known for his orchestral works, including his "Pacific 231" and "Symphony No. 3."
            Frank Martin: He was a composer and conductor who lived from 1890 to 1974. He is known for his choral works, including his "Mass for Double Choir" and "Songs of Ariel."
            Othmar Schoeck: He was a composer and conductor who lived from 1886 to 1957. He is known for his vocal works, including his "Notturno" and "Elegie."
            Joachim Raff: He was a composer who lived from 1822 to 1882. He is known for his orchestral works, including his "Symphony No. 3" and "Lenore Symphony."
            These are just a few examples of the many talented Swiss composers throughout history.
          The William Tell Overture is a musical composition by Gioachino Rossini. It was written in 1829 and is best known for its famous finale, which is often used in popular culture to depict excitement and action. The overture was originally written as an introduction to Rossini\'s opera, William Tell, which tells the story of a Swiss folk hero who fights against Austrian oppression. The overture features a variety of musical themes, including a famous trumpet fanfare and a fast-paced gallop. It has been used in numerous films, TV shows, and commercials, and is considered one of the most recognizable pieces of classical music.
          Opera is a form of musical theater that originated in Italy in the late 16th century. It combines singing, acting, and orchestral music to tell a story. The performers in opera use their voices to convey the emotions and actions of the characters they are portraying. The music in opera is typically very dramatic and emotional, and often includes arias, duets, and choruses. Some of the most famous operas include "The Marriage of Figaro," "Carmen," and "La Traviata." Opera is still performed around the world today, and many people consider it to be one of the most beautiful and powerful forms of art.
          Archery is a sport that involves using a bow and arrow to shoot at a target. It requires a great deal of skill, precision, and focus. Archery can be practiced both indoors and outdoors, and can be enjoyed by people of all ages and abilities. The sport has a rich history, dating back to ancient times when it was used for hunting and warfare. Today, archery is a popular competitive sport, with events held at the local, national, and international levels. It requires a combination of physical and mental strength, as well as patience and discipline. Archery is a great way to improve hand-eye coordination, balance, and overall fitness. It is also a fun and challenging activity that can be enjoyed alone or with others. #sport
        Demo questions - The following questions show various aspects of how Query Chroma responds given the Sample notes. Try selecting a question and then cmd-K "Query Chroma"
          What do I know about archery?
          What do I know about archery? #sport
          What do I know about archery used in wars?
          What do I know about philosophers?
          Do I know anything about famous legendary figures?
      Tana Weaviate Experiments
        What is this?
          These commands take Tana nodes (+context) and add them to the Weaviate vector database. This is done by first passing them to OpenAI to generate an embedding (a vector with 1536 dimensions). This vector is then inserted into Weaviate with the Tana nodeId as the key.
          Weaviate allows us to then query for "similar nodes", each with a "confidence" relative to our query. The query is also just a Tana node, converted into an embedding by OpenAI. The richer the query, the better the vector search should be in theory.
          Importantly, this is not ChatGPT-style "completions". It\'s a form of search for your own Tana content. It won\'t find (or generate) things you don\'t already know.
        Setup
          You\'ll need an OpenAI API Key to use this. You should be prompted to save this safely in your local Tana environment when you first use the commands.
          These commands rely on the TanaHelper service. You can run tana-helper as a local service. Grab the code from github (follow README instructions. Needs developer knowledge). If you do this, make sure to turn on the Avoid Proxy flag in all three Chroma commands below.
          To make it easier to setup you server base URL, I\'ve used the Tana support for secrets. The first time you run one of these commands in Tana, you\'ll be prompted to fill in the value for the HelperURL. If you are running locally, use <a href="http://localhost:8000">http://localhost:8000</a> (or whatever port you\'re running on). For server deployments of the tana-helper service, configure appropriately per the instructions on Github.
        Commands: There are four Weaviate commands implemented.
          Update - which stores the Tana node (with all children as context data) as an embedding in Weaviate
            Update Weaviate embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  URL:: ${secret:HelperURL}/weaviate/upsert
                  Parse result:: Disregard (don\'t insert)
                  Headers:: Content-Type: application/json
                  Payload:: { "openai": "${secret:OpenAIKey}", "nodeId": "${sys:nodeId}", "tags": "${sys:tags}", "context": "${sys:context}"}
                  API method:: POST
          Query - which takes your current node, turns it into an embedding and then finds all semantically similar nodes in Weaviate.
            Query Weaviate embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  URL:: ${secret:HelperURL}/weaviate/query
                  Parse result:: Tana Paste
                  Headers:: Content-Type: application/json
                  Payload:: { "openai": "${secret:OpenAIKey}", "nodeId": "${sys:nodeId}", "tags": "${sys:tags}", "score": "0.78", "context": "${sys:context}"}
                  API method:: POST
          Remove - which takes your current node and simply deletes it from Weaviate.
            Remove Weaviate embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  URL:: ${secret:HelperURL}/weaviate/delete
                  Parse result:: Disregard (don\'t insert)
                  Headers:: Content-Type: application/json
                  Payload:: { "nodeId": "${sys:nodeId}" }
                  API method:: POST
          Purge - which removes all content from your Weaviate instance
            Purge Weaviate
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  URL:: ${secret:HelperURL}/weaviate/purge
                  Parse result:: Disregard (don\'t insert)
                  Headers:: Content-Type: application/json
                  Payload:: { }
                  API method:: POST
        [[Demo topics^Z31PXMKCf8wK]]
          William Tell is a legendary Swiss folk hero who is known for his incredible archery skills and his role in the Swiss struggle for independence. According to legend, William Tell was a skilled archer who lived in the early 14th century in the canton of Uri, Switzerland. The region was under the control of the Habsburgs, who were known for their oppressive rule and high taxes.
          One day, William Tell was approached by a Habsburg official who demanded that he shoot an apple off of his son\'s head with his bow and arrow. If he refused or missed, both he and his son would be executed. William Tell successfully shot the apple off of his son\'s head, but was arrested for carrying a concealed weapon. He was sentenced to death, but managed to escape and went on to lead a rebellion against the Habsburgs
          The story of William Tell has become a symbol of Swiss independence and resistance against tyranny. It has been retold in countless books, plays, and movies, and his image can be found on everything from coins to postage stamps.
          Archery has a long and rich history that dates back to ancient times. The earliest evidence of archery dates back to around 10,000 BC, when the first bows were made from materials such as wood, bone, and sinew. Archery was used for hunting and warfare, and it quickly became an important skill for many cultures around the world.
          In ancient Egypt, archery was used for hunting and in warfare. The Egyptians used composite bows made from layers of wood, horn, and sinew, which were highly effective in battle. In ancient Greece, archery was also used in warfare, but it was also an important sport. The Greeks held archery competitions during the Olympic Games, and archery was considered a noble pursuit.
          In medieval Europe, archery was an important part of warfare. The English longbow was a powerful weapon that could penetrate armor, and it played a key role in many battles, including the Battle of Agincourt in 1415. Archery was also an important sport in medieval Europe, and archery competitions were held throughout the continent.
          Today, archery is still a popular sport and hobby. It is also used in hunting and in some forms of warfare. Modern archery equipment has come a long way from the simple bows of ancient times, and there are now many different types of bows and arrows available for different purposes.
          Philosophy is a branch of knowledge that deals with fundamental questions about existence, reality, knowledge, values, reason, mind, and language. It seeks to understand the nature of the world and our place in it, as well as to explore the meaning and purpose of life. Philosophers use critical thinking, logic, and argumentation to analyze and evaluate different ideas and theories, and to develop their own perspectives on these issues. Some of the major areas of philosophy include metaphysics, epistemology, ethics, political philosophy, and aesthetics.
          Greek archery was an important aspect of ancient Greek warfare. The Greeks used a type of bow called the composite bow, which was made of layers of wood, horn, and sinew. These bows were powerful and could shoot arrows over long distances. Greek archers were often used as skirmishers, harassing enemy troops with arrows before the main battle. They were also used to defend fortifications and ships. The most famous Greek archers were the Cretan archers, who were known for their skill and accuracy. Archery was also an important sport in ancient Greece, with competitions held at the Olympic Games.
          Switzerland has a rich history of classical music and has produced many notable composers. Some of the most famous Swiss composers include:
            Arthur Honegger: He was a prominent composer in the early 20th century and is known for his orchestral works, including his "Pacific 231" and "Symphony No. 3."
            Frank Martin: He was a composer and conductor who lived from 1890 to 1974. He is known for his choral works, including his "Mass for Double Choir" and "Songs of Ariel."
            Othmar Schoeck: He was a composer and conductor who lived from 1886 to 1957. He is known for his vocal works, including his "Notturno" and "Elegie."
            Joachim Raff: He was a composer who lived from 1822 to 1882. He is known for his orchestral works, including his "Symphony No. 3" and "Lenore Symphony."
            These are just a few examples of the many talented Swiss composers throughout history.
          The William Tell Overture is a musical composition by Gioachino Rossini. It was written in 1829 and is best known for its famous finale, which is often used in popular culture to depict excitement and action. The overture was originally written as an introduction to Rossini\'s opera, William Tell, which tells the story of a Swiss folk hero who fights against Austrian oppression. The overture features a variety of musical themes, including a famous trumpet fanfare and a fast-paced gallop. It has been used in numerous films, TV shows, and commercials, and is considered one of the most recognizable pieces of classical music.
          Opera is a form of musical theater that originated in Italy in the late 16th century. It combines singing, acting, and orchestral music to tell a story. The performers in opera use their voices to convey the emotions and actions of the characters they are portraying. The music in opera is typically very dramatic and emotional, and often includes arias, duets, and choruses. Some of the most famous operas include "The Marriage of Figaro," "Carmen," and "La Traviata." Opera is still performed around the world today, and many people consider it to be one of the most beautiful and powerful forms of art.
          Archery is a sport that involves using a bow and arrow to shoot at a target. It requires a great deal of skill, precision, and focus. Archery can be practiced both indoors and outdoors, and can be enjoyed by people of all ages and abilities. The sport has a rich history, dating back to ancient times when it was used for hunting and warfare. Today, archery is a popular competitive sport, with events held at the local, national, and international levels. It requires a combination of physical and mental strength, as well as patience and discipline. Archery is a great way to improve hand-eye coordination, balance, and overall fitness. It is also a fun and challenging activity that can be enjoyed alone or with others. #sport
        [[Demo questions^bIsEyBkQvyG3]]
          What do I know about archery?
          What do I know about archery? #sport
          What do I know about archery used in wars?
          What do I know about philosophers?
          Do I know anything about famous legendary figures?
      Tana Pinecone Experiments
        What is this?
          These commands take Tana nodes (+context) and add them to the Pinecone vector database. This is done by first passing them to OpenAI to generate an embedding (a vector with 1536 dimensions). This vector is then inserted into Pinecone with the Tana nodeId as the key.
          Pinecone allows us to then query for "similar nodes", each with a "score" relative to our query. The query is also just a Tana node, converted into an embedding by OpenAI. The richer the query, the better the vector search should be in theory.
          Importantly, this is not ChatGPT-style "completions". **_It\'s a form of search for your own Tana content._** It won\'t find (or generate) things you don\'t already know. 
          Demo video [[CleanShot 2023-04-17 at 10.41.40-converted^VszdSWVYck]]
        Setup
          You\'ll need a Pinecone API Key and an OpenAI API Key to use this. You should be prompted to save these safely in your local Tana environment when you first use the commands.
          These commands rely on the TanaHelper service. You can run tana-helper as a local service. Grab the code from github (follow README instructions. Needs developer knowledge). If you do this, make sure to turn on the Avoid Proxy flag in all three Pinecone commands below.
          To make it easier to setup you server base URL, I\'ve used the Tana support for secrets. The first time you run one of these commands in Tana, you\'ll be prompted to fill in the value for the HelperURL. If you are running locally, use <a href="http://localhost:8000">http://localhost:8000</a> (or whatever port you\'re running on). For server deployments of the tana-helper service, configure appropriately per the instructions on Github.
        Commands: There are three Pinecone commands implemented. 
          Update - which stores the Tana node (with all children as context data) as an embedding in Pinecone
            Update Pinecone embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  API method:: POST
                  URL:: ${secret:HelperURL}/pinecone/upsert
                  Parse result:: Disregard (don\'t insert)
                  Headers:: Content-Type: application/json
                  Payload:: 
                    { 
                      "pinecone": "${secret:Pinecone}",
                      "openai": "${secret:OpenAIKey}",
                      "nodeId": "${sys:nodeId}",  
                      "tags": "${sys:tags}", 
                      "context": "${sys:context}"  
                    }
          Query - which takes your current node, turns it into an embedding and then finds all semantically similar nodes in Pinecone. 
            Query Pinecone embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  API method:: POST
                  URL:: ${secret:HelperURL}/pinecone/query
                  Parse result:: Tana Paste
                  Headers:: Content-Type: application/json
                  Payload:: 
                    {
                      "openai": "${secret:OpenAIKey}",
                      "pinecone": "${secret:Pinecone}",
                      "nodeId": "${sys:nodeId}",
                      "tags": "${sys:tags}",
                      "score": "0.78",
                      "context": "${sys:context}"
                    }
          Remove - which takes your current node and simply deletes it from Pinecone.
            Remove Pinecone embedding
              Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
                **Associated data**
                  Avoid using proxy:: [X] 
                  Parse result:: Disregard (don\'t insert)
                  URL:: ${secret:HelperURL}/pinecone/delete
                  Payload:: 
                    {
                      "pinecone": "${secret:Pinecone}",
                      "openai": "${secret:OpenAIKey}",
                      "nodeId": "${sys:nodeId}"
                    }
                  Headers:: Content-Type: application/json
                  API method:: POST
        [[Demo topics^Z31PXMKCf8wK]]
          William Tell is a legendary Swiss folk hero who is known for his incredible archery skills and his role in the Swiss struggle for independence. According to legend, William Tell was a skilled archer who lived in the early 14th century in the canton of Uri, Switzerland. The region was under the control of the Habsburgs, who were known for their oppressive rule and high taxes.
          One day, William Tell was approached by a Habsburg official who demanded that he shoot an apple off of his son\'s head with his bow and arrow. If he refused or missed, both he and his son would be executed. William Tell successfully shot the apple off of his son\'s head, but was arrested for carrying a concealed weapon. He was sentenced to death, but managed to escape and went on to lead a rebellion against the Habsburgs
          The story of William Tell has become a symbol of Swiss independence and resistance against tyranny. It has been retold in countless books, plays, and movies, and his image can be found on everything from coins to postage stamps.
          Archery has a long and rich history that dates back to ancient times. The earliest evidence of archery dates back to around 10,000 BC, when the first bows were made from materials such as wood, bone, and sinew. Archery was used for hunting and warfare, and it quickly became an important skill for many cultures around the world.
          In ancient Egypt, archery was used for hunting and in warfare. The Egyptians used composite bows made from layers of wood, horn, and sinew, which were highly effective in battle. In ancient Greece, archery was also used in warfare, but it was also an important sport. The Greeks held archery competitions during the Olympic Games, and archery was considered a noble pursuit.
          In medieval Europe, archery was an important part of warfare. The English longbow was a powerful weapon that could penetrate armor, and it played a key role in many battles, including the Battle of Agincourt in 1415. Archery was also an important sport in medieval Europe, and archery competitions were held throughout the continent.
          Today, archery is still a popular sport and hobby. It is also used in hunting and in some forms of warfare. Modern archery equipment has come a long way from the simple bows of ancient times, and there are now many different types of bows and arrows available for different purposes.
          Philosophy is a branch of knowledge that deals with fundamental questions about existence, reality, knowledge, values, reason, mind, and language. It seeks to understand the nature of the world and our place in it, as well as to explore the meaning and purpose of life. Philosophers use critical thinking, logic, and argumentation to analyze and evaluate different ideas and theories, and to develop their own perspectives on these issues. Some of the major areas of philosophy include metaphysics, epistemology, ethics, political philosophy, and aesthetics.
          Greek archery was an important aspect of ancient Greek warfare. The Greeks used a type of bow called the composite bow, which was made of layers of wood, horn, and sinew. These bows were powerful and could shoot arrows over long distances. Greek archers were often used as skirmishers, harassing enemy troops with arrows before the main battle. They were also used to defend fortifications and ships. The most famous Greek archers were the Cretan archers, who were known for their skill and accuracy. Archery was also an important sport in ancient Greece, with competitions held at the Olympic Games.
          Switzerland has a rich history of classical music and has produced many notable composers. Some of the most famous Swiss composers include:
            Arthur Honegger: He was a prominent composer in the early 20th century and is known for his orchestral works, including his "Pacific 231" and "Symphony No. 3."
            Frank Martin: He was a composer and conductor who lived from 1890 to 1974. He is known for his choral works, including his "Mass for Double Choir" and "Songs of Ariel."
            Othmar Schoeck: He was a composer and conductor who lived from 1886 to 1957. He is known for his vocal works, including his "Notturno" and "Elegie."
            Joachim Raff: He was a composer who lived from 1822 to 1882. He is known for his orchestral works, including his "Symphony No. 3" and "Lenore Symphony."
            These are just a few examples of the many talented Swiss composers throughout history.
          The William Tell Overture is a musical composition by Gioachino Rossini. It was written in 1829 and is best known for its famous finale, which is often used in popular culture to depict excitement and action. The overture was originally written as an introduction to Rossini\'s opera, William Tell, which tells the story of a Swiss folk hero who fights against Austrian oppression. The overture features a variety of musical themes, including a famous trumpet fanfare and a fast-paced gallop. It has been used in numerous films, TV shows, and commercials, and is considered one of the most recognizable pieces of classical music.
          Opera is a form of musical theater that originated in Italy in the late 16th century. It combines singing, acting, and orchestral music to tell a story. The performers in opera use their voices to convey the emotions and actions of the characters they are portraying. The music in opera is typically very dramatic and emotional, and often includes arias, duets, and choruses. Some of the most famous operas include "The Marriage of Figaro," "Carmen," and "La Traviata." Opera is still performed around the world today, and many people consider it to be one of the most beautiful and powerful forms of art.
          Archery is a sport that involves using a bow and arrow to shoot at a target. It requires a great deal of skill, precision, and focus. Archery can be practiced both indoors and outdoors, and can be enjoyed by people of all ages and abilities. The sport has a rich history, dating back to ancient times when it was used for hunting and warfare. Today, archery is a popular competitive sport, with events held at the local, national, and international levels. It requires a combination of physical and mental strength, as well as patience and discipline. Archery is a great way to improve hand-eye coordination, balance, and overall fitness. It is also a fun and challenging activity that can be enjoyed alone or with others. #sport
        [[Demo questions^bIsEyBkQvyG3]]
          What do I know about archery?
          What do I know about archery? #sport
          What do I know about archery used in wars?
          What do I know about philosophers?
          Do I know anything about famous legendary figures?
  ð\x9f\x93\x8c Harvesting inline references
    This section contains commands to push a single node to one or more inlines references that the node contains. There are two commands involved and a small helper function provided by the <code>tana-helper</code> service. (Source code at [[GitHub - verveguy/tana-helper^955M39GifZ]])
    Use case: While in a meeting, you are taking notes on various topics, and you reference the topics inline in these notes. The meeting is a day/time/place oriented structure that is complete once the meeting is over. The topics you discussed however are quite probably ongoing, or even "evergreen". At the end of the meeting, you wish to push the various notes you took to the nodes that represent each topic discussed.
    [[Video Explainer^kM-sMuhr7s]]
    Example scenarios
      Topics that are long-lived
        Upcoming Holiday Party #event
        Really tricky customer project #project
        Highly confidential invention #patent
      Meetings
        Weekly staff meeting with John and Jill #meeting
          Date:: [[date:2023-05-28]]
          Time:: 15:00
          Place:: Somewhere
          Attendees:: 
            John
            Jill
            Jack
          Tasks:: Many Tasks #project
          We started with a round of hellos and personal catch ups. John has a new partner. Congrats, John!
          
          The [[Really tricky customer project^x429_ebP8I]]is having some problems. It seems that the project scope wasn\'t properly defined early on and now we\'re facing serious over runs due to scope creep.
          
          Our [[Upcoming Holiday Party^Lu4aEmn1uS]]is on track although there are problems with the entertainment. Seems we can\'t get the act we originally wanted as so Jack is looking for alternatives.
          Jill presented an update on the [[Highly confidential invention^CnJ65yO0pI]]and noted that we really want the patent application to be filed before the [[Upcoming Holiday Party^Lu4aEmn1uS]]so that we can make a big announcement to all the staff at the event.
          [[A node that can be referenced^rT7L9GWNdU]]
            Time:: Tomorrow
            Place:: Nowhere in particular
        Unplanned meeting with Dave and Jack #meeting
          Date:: [[date:2023-05-28]]
          Time:: 15:00
          Place:: Somewhere
          Attendees:: 
            Dave
            Jack
          Tasks:: Many Tasks #project
          Houston, we have a problem.
            Said someone, once.
            [[A node that can be referenced^rT7L9GWNdU]]
              Time:: Tomorrow
              Place:: Nowhere in particular
    Commands: There are two commands implemented:
      Find inline refs - This command finds all inline refs in a given node and adds them as node references to a field named `inline refs`. This field is intended to be used by related the Push node to inline ref command. This command uses the tana-helper server to actually extract the inline references. Note that one inline ref field is added per inline ref which might seem off at first but is important to the operation of the Push node command.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/inlinerefs
            Avoid using proxy:: [X] 
            API method:: POST
            Headers:: Content-Type: application/json
            Payload:: 
              {
                "nodeId": "${sys:nodeId}",
                "context": "${sys:context}"
              }
            Insert output strategy:: as child
            Parse result:: Tana Paste
      Push node to inline ref - This command grabs one of the inline ref fields on the current node and moves the current node to the node referenced by the inline ref field. It then removes the inline ref field itself. If the current node has no inline ref fields, it does nothing.
        Move node - System command. Params: *Move node target, Remove reference after moving node, Move original node
          **Associated data**
            Target node:: 
              Lookup field:: 
                inline ref #field-definition
                  Optional:: [X] 
                  Cardinality:: Single value - Only one item allowed
                  Datatype:: Plain - A list with one or more items
                  Autocollect options:: [ ] 
                  Hide field conditions:: Never - Never hide this field
                  Semantic function:: None - No value set
                  Formula:: [ ] 
                  Shared definition:: [ ] 
            Remove reference after moving node:: [ ] 
        Remove fields - System command. Params: *Fields to remove
          **Associated data**
            Fields to remove:: [[inline ref^OZnkAw2Ktl]]
    patent #supertag
    event #supertag
    project #supertag
    meeting #supertag
  ð\x9f\x90\x8d Running user-defined python
    There\'s been many times when I\'ve wished Tana had a way to just "run some code". The ability of OpenAI to kinda do code-like things has been great, but I still want the predictability (and speed!) of simple coded solutions for many things. 
    So saying, I decided to add a little function to the <code>tana-helper</code> that lets the user craft a Tana command that runs an arbitrary chunk of python code against some passed in params.
    [[Video Explainer^qce2WeKDZr]]
    Commands. There are three commands involved:
      User function with inline code (CURRENTLY BROKEN \
HANDLING BY TANA)
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/exec
            API method:: POST
            Avoid using proxy:: [X] 
            Headers:: Content-Type: application/json
            Payload:: 
              {
                "code": "def ref_from_node(node):\
return \'[[^\'+node+\']]\'",
                "call": "\'This was interesting \'+ref_from_node(nodeId)",
                "payload": {
                  "context": "${sys:context}",
                  "nodeId": "${sys:nodeId}"
                }
              }
      User function with loose inline code
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/exec_loose
            API method:: POST
            Avoid using proxy:: [X] 
            Payload:: 
              Code:
```python
import re

def do_something():
  result = \'Welcome to \'+something+\' [[^\'+ nodeId + \']]\'
  return result
```
              Params:
                {
                "context": "${sys:context}",
                "nodeId": "${sys:nodeId}",
                "something": "${something|?}"
                }
              Call:
```python
do_something()
```
      User function with indirect code
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/exec
            API method:: POST
            Avoid using proxy:: [X] 
            Headers:: Content-Type: application/json
            Insert output strategy:: as child
            Payload:: 
              {
                "code": "${code}",
                "call": "${call}",
                "payload": {
                  "context": "${sys:context}",
                  "nodeId": "${sys:nodeId}",
                  "something": "${something|?}"
                }
              }
    Examples
      Hello, world! using inline code
      Hello, world! using loose inline code
        something:: (A different time and place)
      Hello, world! using indirect code. Note: if you use Tana code blocks, you must select "python" as the language. Otherwise, the helper service won\'t know to remove it from the code before evaluating it.
        code:: 
```python
import re

def do_something():
  result = \'Welcome to \'+something+\' [[^\'+ nodeId + \']]\'
  return result
```
           call:: 
```python
do_something()
```
        something:: (another time and place)
    Dynamic templates 
      One thing that is hard to do in Tana is have a tag chosen indirectly. Andre Foeken was trying to do this recently so I used the Tana helper feature to solve the problem in one way.
      Brett Adam #person
    
      Add 1:1 meeting
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/exec_loose
            Avoid using proxy:: [X] 
            API method:: POST
            Payload:: 
              Call:
```python
do_something()
```
                 Params:
                   {
                   "name": "${name}",
                   "tag": "${meeting tag}"
                   }
                 Code:
```python
import re #not actually needed

def do_something():
  result = \'- Meeting with [[\'+name+\']] #[[\'+ tag + \']]\'
  return result
```
            Parse result:: Tana Paste
            Insert output strategy:: as sibling
  ð\x9fª\x9d Automagic Webhooks for Tana Input API
    Based on the inspiring example from @houshuang (see <a href="https://share.cleanshot.com/PNDJjGp4">recording</a>), tana-helper now provides a powerful form of webhook processing.
    Basically, you can shovel any text, email, etc at the /webhook/<tana_type> endpoint and it will process it into JSON using OpenAI and push the resulting JSON into Tana via the <a href="https://help.tana.inc/tana-input-api.html">Tana Input API</a>.
    So you can call this webhook from pretty much any integration platform such as Zapier or for email, use the <a href="https://cloudmailin.com/">cloudmailin.com</a> service as @houshuang did.
    But how does the external service reach my local [[tana-helper^suaygeUMX-ek]]service? Using something like ngrok you can open a tunnel back to your local machine, exposing only the tana-helper port 8000.
    Note that when your external service calls these APIs, it must pass your Tana API Token via the _**X-Tana-API-Token**_ HTTP __header otherwise <code>tana-helper</code> will not be able to insert anything into Tana.
    NOTE: So far, I\'ve found that GPT3.5 does very poorly at this task, whereas GPT4 does well.
    Commands
      Create webhook from schema - This command creates a new webhook endpoint in tana-helper, which you can then call to push arbitrary data into Tana via the webhook. You will need to execute this command on a node that has a \'typescript schema\' field that contains the Tana schema of the supertag you wish your webhook to use.When invoked, the webhook will call OpenAI GPT to process the text payload and produce JSON which will be pushed into the Tana Input API. (See Tana documentation on using the Input API for more information).
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/schema/${supertag}
            Avoid using proxy:: [X] 
            API method:: POST
            Headers:: X-Space-App-Key: {$secret:HelperAuthToken}
            Insert output strategy:: replace contents
            Target node:: [[hook URL^ennYkjz0j8]]
            Payload:: ${typescript schema}
    Example:
      The following Tana node and commands allow you to try out the creation of a webhook and then the invocation of it with test data. Note that you will want to update the schema to be your own schema - this is my schema from my instance of this Tana Helper workspace.
      Test webhook locally - This is a local test command to simulate calling the webhook "for real". It will call the webhook URL and push some Tana node data into it which the webhook will then parse via OpenAI GPT into a JSON structure. The JSON will be returned here as well as pushed into the Tana Input API.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${hook URL}
            Avoid using proxy:: [X] 
            API method:: POST
            Headers:: 
              Content-Type: text/plain
              X-Space-App-Key: ${secret:HelperAuthToken}
              X-Tana-API-Token: ${secret:TanaAPIToken}
              X-OpenAI-API-Key: ${secret:OpenAIKey}
            Parse result:: Tana Paste
            Target node:: [[test result^-uK3QAr50a]]
            Payload:: ${test data}
      webhook #supertag
        typescript schema:: 
```typescript
paste as code your schema here
```
         flight #flight
         Add a webhook for flights #webhook
           supertag:: [[flight^6VD3LyFIV5]]
           typescript schema:: 
```typescript
type Node = {
  name: string;
  description:string;
  supertags: [{
    /* flight */
    id: \'6VD3LyFIV5\'
  }];
  children: [
    {
      /* Price */
      type: \'field\';
      attributeId: \'ab4e0ZhLJZ\';
      children: Node[];
    },
    {
      /* Passenger */
      type: \'field\';
      attributeId: \'gyXW-sDZAC\';
      children: Node[];
    },
    {
      /* Arrival time */
      type: \'field\';
      attributeId: \'05lU87Osx9\';
      children: Node[];
    },
    {
      /* Departure time */
      type: \'field\';
      attributeId: \'mIFn7Uyt-G\';
      children: Node[];
    },
    {
      /* To airport */
      type: \'field\';
      attributeId: \'BcuysCHdR_\';
      children: Node[];
    },
    {
      /* From airport */
      type: \'field\';
      attributeId: \'DybG3gf_aT\';
      children: Node[];
    },
  ];
};
```
        hook URL:: http://localhost:8000/webhook/flight
        test data:: 
          Welcome to Hawaii!
          Flight AL 3622
          Leaves BOS at 14:40 on April 1 2023
          Arrives AUA at 18:53 on April 1 2023
          Passengers: Brett Adam, Karanina Minotti, Violet Becker
          Total flight time: 5h30m
    Supertags
      [[sport^9vE-C-Sr4K]]
      [[video.other^IZ60p3x7sB]]
      [[flight^6VD3LyFIV5]]
      [[meeting^XU85eE6riu]]
      [[project^oEk1V0uaww]]
      [[event^_B1vKijVHM]]
      [[patent^5lWhZXXdEQ]]
      [[object^nMkwu40iPm]]
      [[supertag^P9eLBpHjN9]]
        Type A:: Something #person
      [[command^7xT_9vq1oK]]
      [[webhook^On2Ivhod7y]]
        typescript schema:: 
```typescript
paste as code your schema here
```
      [[person^6PQ5J_iCfa]]
        meeting tag:: [[brett meeting^zJDWE8nHsewf]]
      [[website^vvcwkCdh3SxG]]
      [[shared^cV3D2MfcfIMd]]
      [[template^tPum5ope0-0H]]
      
  ð\x9f\x94\xa0 Functions for JSON / Tana Paste bi-directional conversion
    A small command and associated helper service that will take your current node and its full context and convert it to an equivalent JSON structure. Useful perhaps when you then need to pass a JSON structure to some other command. These functions are used elsewhere by Tana helper but I figured they were also useful standalone to save you a round-trip to Chat GPT just to do JSON conversions.
    There are two variations of JSON supported: the first is "Tana JSON" - a set of simple Tana nodes that are structured in a JSON-like structure, one line per Tana node. The second format is actual JSON stored in a formatted Tana node of type "code".
    ð\x9f\x90\x9b Right now, Tana is inconsistent in a variety of ways when it comes to sending Tana structures as payloads. Code blocks in particular are not properly nested so you can\'t preserve their structure. Also when receiving back Tana paste format, Tana treats code blocks in weird ways, again incorrectly nesting them beyond the first level of node structure.
    The Export to JSON command can also be Export to CSV by putting <code>?format=csv</code> on the URL. (if you leave format off, it\'ll default to json)
    Commands
      You will want to modify the Target node of these commands for your use cases - right now, they\'re sert up here for demonstration purposes, populating the various "Output" nodes in the demo seciton below.
      Convert to JSON - Takes a Tana node structure and converts it into the closest logical JSON equivalent. The result is a set of Tana nodes structured as if they were JSON. ("Tana JSON") Make sure to set the Target node to something logical for your use-case.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/jsonify
            Avoid using proxy:: [X] 
            API method:: POST
            Headers:: X-Space-App-Key: {$secret:HelperAuthToken}
            Parse result:: Insert as raw (default)
            Insert output strategy:: as child
            Target node:: [[Output node for convert to JSON command^dNSIJAY9kn]]
            Payload:: 
              ${sys:context}
      Export to JSON - Take a regular Tana node structure and converts it into the closet logical JSON equivalent. Saves the results to a temporary file on the tana-helper server. (Typically localhost:/tmp/tana-helper/export/). Also allows for CSV with format=csv query param.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/export/outfile?format=json
            Avoid using proxy:: [X] 
            API method:: POST
            Parse result:: Disregard (don\'t insert)
            Payload:: 
              ${sys:context}
      Convert to Tana - Takes a Tana JSON structure and converts it into the logical Tana paste equivalent without requiring roundtrips to Open AI.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/tanify
            Avoid using proxy:: [X] 
            API method:: POST
            Parse result:: Tana Paste
            Target node:: [[Output for convert to Tana^slkyMvtRFa]]
            Payload:: ${sys:context}
      Convert to JSON code node - Converts the Tana node structure to JSON and then returns the result as a Tana node formatted as code.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/tana-to-code
            Avoid using proxy:: [X] 
            API method:: POST
            Parse result:: Tana Paste
            Insert output strategy:: as child
            Target node:: [[Output node for convert to code node command^L976VgpeRp]]
            Payload:: 
              ${sys:context}
      Convert code node to JSON - Converts a Tana code node to an equivalent set of Tana nodes formatted in Tana-JSON representation.
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/code-to-json
            Avoid using proxy:: [X] 
            API method:: POST
            Parse result:: Insert as raw (default)
            Insert output strategy:: as child
            Target node:: [[Output node for convert to JSON command^dNSIJAY9kn]]
            Payload:: ${sys:content}
    Demonstration
      Testing JSON / TANA conversion commands
      Test node for conversions - try this Search code
      Meetings
        [[ Weekly staff meeting with John and Jill^Ac8m-TBxu9]]
          Date:: [[date:2023-05-28]]
          Time:: 15:00
          Place:: Somewhere
          Attendees:: 
            John
            Jill
            Jack
          Tasks:: Many Tasks #project
          We started with a round of hellos and personal catch ups. John has a new partner. Congrats, John!
          
          The [[Really tricky customer project^x429_ebP8I]]is having some problems. It seems that the project scope wasn\'t properly defined early on and now we\'re facing serious over runs due to scope creep.
          
          Our [[Upcoming Holiday Party^Lu4aEmn1uS]]is on track although there are problems with the entertainment. Seems we can\'t get the act we originally wanted as so Jack is looking for alternatives.
          Jill presented an update on the [[Highly confidential invention^CnJ65yO0pI]]and noted that we really want the patent application to be filed before the [[Upcoming Holiday Party^Lu4aEmn1uS]]so that we can make a big announcement to all the staff at the event.
          [[A node that can be referenced^rT7L9GWNdU]]
        [[Unplanned meeting with Dave and Jack^kP7njALYgn]]
          Date:: [[date:2023-05-28]]
          Time:: 15:00
          Place:: Somewhere
          Attendees:: 
            Dave
            Jack
          Tasks:: Many Tasks #project
          Houston, we have a problem.
            Said someone, once.
            [[A node that can be referenced^rT7L9GWNdU]]
      A node that can be referenced
        Time:: Tomorrow
        Place:: Nowhere in particular
      Output node for convert to JSON command
      Output node for convert to code node command
      Output for convert to Tana
      Demo data
        Meetings
          [[ Weekly staff meeting with John and Jill^Ac8m-TBxu9]]
            Date:: [[date:2023-05-28]]
            Time:: 15:00
            Place:: Somewhere
            Attendees:: 
              John
              Jill
              Jack
            Tasks:: Many Tasks #project
            We started with a round of hellos and personal catch ups. John has a new partner. Congrats, John!
            The [[Really tricky customer project^x429_ebP8I]]is having some problems. It seems that the project scope wasn\'t properly defined early on and now we\'re facing serious over runs due to scope creep.
            Our [[Upcoming Holiday Party^Lu4aEmn1uS]]is on track although there are problems with the entertainment. Seems we can\'t get the act we originally wanted as so Jack is looking for alternatives.
            Jill presented an update on the [[Highly confidential invention^CnJ65yO0pI]]and noted that we really want the patent application to be filed before the [[Upcoming Holiday Party^Lu4aEmn1uS]]so that we can make a big announcement to all the staff at the event.
            [[A node that can be referenced^rT7L9GWNdU]]
              Time:: Tomorrow
              Place:: Nowhere in particular
          [[Unplanned meeting with Dave and Jack^kP7njALYgn]]
            Date:: [[date:2023-05-28]]
            Time:: 15:00
            Place:: Somewhere
            Attendees:: 
              Dave
              Jack
            Tasks:: Many Tasks #project
            Houston, we have a problem.
              Said someone, once.
              [[A node that can be referenced^rT7L9GWNdU]]
                Time:: Tomorrow
                Place:: Nowhere in particular
    Bugs
      A complex example that shows various bugs in Tana send and receive handling
        Code:: 
```javascript
This is a block of code
multiple lines
Trying this out to see what happens
Oh boy!
  if trash_node is not None:
    trash_children = trash_node.children
    if trash_children:
      for node_id in trash_children:
        if node_id in index:
          trash[node_id] = index[node_id]
          #del index[node_id]
```
        Next field:: 
          Something good
            With nested children
            And more children
              A field:: 
                With some value
                  And another value
                    A field:: 
                      A field:: A
                      Next field:: B
                      C
                    Next field:: D
                    E
```python
This is a block of code
multiple lines
Trying this out to see what happens
Oh boy!
  if trash_node is not None:
    trash_children = trash_node.children
    if trash_children:
      for node_id in trash_children:
        if node_id in index:
          trash[node_id] = index[node_id]
          #del index[node_id]
```
              And another node
              language:: Out of order fields
            With some random children
          All for the good
        And the bettermemt of my friends
          A field:: Another value
      
  ð\x9f\x9aª Tana Helper as JSON proxy gateway
    This is a small demo of how you can use the tana-helper service to act as a proxy gateway to other API endpoints, converting Tana nodes to JSON on the way out, and converting JSON responses back to Tana paste format on the way back. It uses the functions in the [[ð\x9f\x94\xa0 Functions for JSON / Tana Paste bi-directional conversion^LLliYxGNev]]section to do the conversions.
    The demo uses tana-helper as a proxy to the [[restful-api.dev^BtKrftGtdk]]service to simply POST Tana structures to their free "database in the sky". Try this with your own API endpoints and [[let me know^IoGXeGbU4a]]how you make out 
    Use this API to call external services. The URL pattern is /proxy/<code><METHOD></code>/<code><TARGET URL></code>. So /proxy/DELETE/http://something.com/foo?id=12 will make. a DELETE request to whatever is at http://something.com/foo?id=12
    [[Video Explainer^-XUN7_rULT]]
    restful-api.dev call via proxy - Use this API to call external services. The URL pattern is /proxy/<method>/<target URL>. So /proxy/DELETE/http://something.com/foo?id=12 will make. a DELETE request to whatever is at http://something.com/foo?id=12 
      Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
        **Associated data**
          URL:: ${secret:HelperURL}/proxy/POST/https://api.restful-api.dev/objects
          Avoid using proxy:: [X] 
          Payload:: Tana Paste of whole node
          API method:: POST
          Insert output strategy:: as sibling
          Parse result:: Tana Paste
    This is a RESTful data object.  We pass a Tana structure as the value of data field
      data:: 
        Another object
          field 1:: Foo
          field 2:: Bar
    What this looks like as JSON to the upstream restful-api.dev service:
```json
{
    "name": "This is a RESTful data object.  We pass a Tana structure as the value of data field",
    "data": [
        {
            "name": "Another object",
            "field 1": "Foo",
            "field 2": "Bar"
        }
    ]
}
```
    This is a RESTful  object in Tana. Note the data field has fields
      data:: 
        api_key:: none
        format:: text
        target:: de
        source:: auto
        q:: What on earth does this do?
    What this node looks like to the upstream service...
```json
{
    "name": "This is a RESTful  object in Tana. Note the data field has fields",
    "data": {
        "api_key": "none",
        "format": "text",
        "target": "de",
        "source": "auto",
        "q": "What on earth does this do?"
    }
}
```
  ð\x9f\x8c\x83 Tana Visualizer
    Inspired by the original marketing visualization on the Tana.inc website, <code>tana-helper</code> provides a 3D visualization of your Tana workspace.
    [[Interactive 3D visualization of my Tana knowledge graph^x3kjJ-w4rNou]]
      Recording: [[CleanShot 2023-06-08 at 22.13.31^cqNhPRTCNUN1]]
    How do I use it? Go to [[http://localhost:8000/ui^7z3X7AllejDH]]and you will be presented with the Visualizer webapp. You can upload your most recent Tana JSON export and then play with the visualization.
    Check out this <a href="https://share.cleanshot.com/7J6d6F6l">video demo</a>
  ð\x9f\x93¥ Tana Paste Input Queue
    After getting tired of being unable to send Tana Paste formatted text via the Tana Input API, I decided to do something about this. Hopefully at some point, Tana will close this gap but until then, this is a workaround that lets you push Tana Paste into Tana from anywhere that can reach your tana-helper service.
    The basic strategy is that you call a <code>tana-helper</code> API to "queue up" the paste which adds a special queue node to your Tana Inbox. Later on when back in the Tana UI, you use a Tana <code>Make API request</code> command to "fetch" the queued paste. This is the only way to get Tana paste into Tana currently via a push API.
    The first use-case for this was ChatGPT. Using the new Custom GPT feature, you can build a GPT that can format answers in Tana paste format making up fields, tags, etc. as required.  By configuring your GPT to know about the tana-helper Enqueue Entry API, you can have ChatGPT sending data directly into Tana.
    Now, since <code>tana-helper</code> is mostly intended to be a local service these days, you need to expose your Tana helper service via something like ngrok for this to work from the outside world. Be careful: there\'s currently no security on tana-helper (yet - I\'m working on it).
    [[But how does the external service reach my local tana-helper service? Using something like ngrok you can open a tunnel back to your local machine, exposing only the tana-helper port 8000.^4XQ-tvR_mSfr]]
    [[Note that when your external service calls these APIs, it must pass your Tana API Token via the X-Tana-API-Token HTTP header otherwise tana-helper will not be able to insert anything into Tana.^cTEDlE4k-0]]
    Commands
      There\'s really only one Tana command needed - Fetch Queued Entry. The other API is documented here as if it were a command, but Enqueue is only needed by external systems that generate Tana paste format output and want to push it into Tana.
      Fetch Queued Entry #command
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/chroma/dequeue
            Avoid using proxy:: [X] 
            Parse result:: Tana Paste
            Headers:: Content-Type: application/json
            Payload:: {"context": "${sys:context}"}
            API method:: POST
            Insert output strategy:: replace contents
      Enqueue Entry #command - This is merely for documentation - call this from outside Tana, sending Tana Paste text in the body (payload)
        Make API request - System command. Params: *URL, Prompt, Target node, Insert output strategy, Payload, API method, Parse result, Authorization header, Headers, Avoid using proxy
          **Associated data**
            URL:: ${secret:HelperURL}/chroma/enqueue
            Avoid using proxy:: [X] 
            Parse result:: Disregard (don\'t insert)
            Headers:: Content-type: plain/text
            Payload:: $context
            API method:: POST
   (demo support stuff)
     flight #supertag
     video.other #supertag
     sport #supertag
   MORE IDEAS
     Update the python helper functions to let you register a function as a code block in the same way you can register a webhook. Save the code block to a file on the service side. Generate an endpoint from the file name just like with a webhook. Then, automatically do the Tana->JSON and JSON->Tana conversions when calling the function.
    
   What do I know about Tana?
     Tana is a system or tool used for taking and organizing notes, likely related to meetings or projects. It appears to use a specific format for creating and referencing notes, with references enclosed in double brackets [[ ]] and containing a note name and identifier separated by the ^ character. The context suggests that Tana may be some sort of intelligent assistant or search engine for accessing this information.
     The new context further indicates that Tana is being used to document discussions, meetings, and decisions related to various projects, such as TechX presentation selections and Capability Map efforts. It also reveals that Tana has the ability to assign tags to notes and has a feature called "ask Tana conversations" which allows users to query the system for specific information using natural language queries.
     Additionally, Tana seems to be integrated with other tools such as Slack, where it\'s used to discuss and document information related to projects and meetings involving individuals like Murtaza Nuruddin Bhori, Craig Huckelbridge, Ian Gray, Tony Arous, Brett, Cornelia Scheitz, Jackeline LeMaitre, and others. Tana is also used to keep track of progress, goals, and tasks for these projects, and to facilitate communication between team members.
     The context also indicates that there are ongoing discussions about improving Tana\'s functionality, such as adding semantic search and creating a clear Slack channel for asking platform-related questions. Overall, Tana seems to be an essential tool for managing and documenting information related to projects and meetings in a work setting where compliance and accountability are important.
     