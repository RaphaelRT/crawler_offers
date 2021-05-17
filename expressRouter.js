const MongoClient = require('mongodb').MongoClient;
const ObjectID = require('mongodb').ObjectID;
const express = require('express');
const path = require('path');
const cors = require("cors");
const spawn = require("child_process").spawn;
const util = require("util");
require('dotenv').config();
const app = express();
const publicPath = __dirname + '/build/';
const NODE_IP = process.env.NODE_IP;
const NODE_PORT = process.env.NODE_PORT;
const MONGO_IP = process.env.MONGO_ALIAS;
const MONGO_PORT = process.env.MONGO_PORT;
const MONGO_DB = process.env.MONGO_DB;

const url = `mongodb://${MONGO_IP}:${MONGO_PORT}/${MONGO_DB}`;
console.log(url)
app.use(express.static(publicPath));

var corsOptions = {
  origin: `http://${NODE_IP}:${NODE_PORT}`
};

app.use(cors(corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
console.warn(publicPath+ "index.html")

app.get('/', function (req,res) {
  res.sendFile(publicPath + "index.html");
});
app.get('/fav', function (req,res) {
  res.sendFile(publicPath + "index.html");
});

app.get('/api/offers', (req, rendered) => {
  MongoClient.connect(url, function(err, db) {
    try{
        if(!err) {
            let collection = db.collection('offers');
            const cursor = collection.find({});
            const allValues = cursor.toArray();
            allValues.then((res, err) => {
                if(!err) {
                  rendered.json(res)
                }
            })
        } else {
          console.log(err)
        }
    } catch {
      if(db) {
        db.close();
      }
    }
  })
});
app.get('/api/offers/fav', (req, rendered) => {
  MongoClient.connect(url, function(err, db) {
    try{
        if(!err) {
            let collection = db.collection('offers');
            const cursor = collection.find({is_fav: true});
            const allValues = cursor.toArray();
            allValues.then((res, err) => {
                if(!err) {
                  rendered.json(res)
                }
            })
        }
    } catch {
      if(db) {
        db.close();
      }
    }
  })
});
app.get('/api/refresh/', function (req,res) {
  
  /*
  async function spawnChild() {
    console.log("BEGIN SCRIPT!")
    const pythonProcess = await spawn('python3', [path.join(__dirname, 'crawler.py')]);
    console.log("SPAWNED!")
    console.log(path.join(__dirname, 'crawler.py'))

    pythonProcess.on('close', function (code) {
      console.log('close: ' + code);
      console.log("Script ended");
    });
   
    pythonProcess.stderr.on('data', function (data) {
        res.writeContinue()
        console.log('stderr: ' + data);
    });
    pythonProcess.stdout.on('data', function (data) {
      res.writeContinue()
      console.log('stdout: ' + data);
    });

    let data = "";
    for await (const chunk of pythonProcess.stdout) {
      console.log('stdout chunk: '+chunk);
      data += chunk;
    }
    let error = "";
    for await (const chunk of pythonProcess.stderr) {
      console.error('stderr chunk: '+chunk);
      error += chunk;
    }
    const exitCode = await new Promise( (resolve, reject) => {
      pythonProcess.on('close', resolve);
    });
    
    if( exitCode) {
        console.log(`subprocess error exit ${exitCode}, ${error}`)
    }
    return data;
  }
  spawnChild().then(
    data=> {console.log("async result:\n" + data);res.json(data.toString('utf8'));},
    err=>  {console.error("async error:\n" + err);}
  );
  */
  //console.log(pythonProcess);
});

app.post('/api/update/:offerId', (req, rendered) => {
  console.log(req.params.offerId)
  console.log(req.body)
  let id = req.params.offerId
  let offer = req.body
  MongoClient.connect(url, function(err, db) {
    try{
        if(!err) {
            let collection = db.collection('offers');
            delete offer['_id']
            console.log(offer)
            const updateOffer = {
              $set: offer,
            };
            let updated = collection.updateOne({_id: ObjectID(id)}, updateOffer);
            updated.then((res, err) => {
              if (!err){
                rendered.json(res)
              }
            })
        }
    } finally {
       db.close();
    }
  })
});

const server = app.listen(NODE_PORT, () => {
  console.log(`Express is running on port http://localhost:${server.address().port}`);
});