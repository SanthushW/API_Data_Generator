const { MongoClient } = require('mongodb');

const uri = ''//replace with url

async function connectToMongoDB() {
  const client = new MongoClient(uri, { 
    tlsAllowInvalidCertificates: true, 
    tlsAllowInvalidHostnames: true,
    serverSelectionTimeoutMS: 5000 
  });

  try {
    await client.connect();
    console.log('Connected to MongoDB successfully');
    return client;
  } catch (error) {
    console.error('Error connecting to MongoDB', error);
    process.exit(1);
  }
}

module.exports = connectToMongoDB;