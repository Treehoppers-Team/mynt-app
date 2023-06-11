const express = require("express");
const bodyParser = require("body-parser");
require("dotenv").config({ path: "../../../.env" });

const {
  getWalletBalanceFirebase,
  getTransactionHistoryFirebase,
  getUserFirebase,
  insertUserFirebase,
  updateUserBalanceFirebase,
  insertTransactionFirebase,
  updateBankBalanceFirebase,
  updateRegistrationFirebase,
  getEventsFirebase,
  getEventRegistrationsFirebase,
  getRegistrationsFirebase,
  getAllRegistrationsFirebase,
  insertRegistrationFirebase,
  mintNft,
  getUserWalletFirebase,
  getNftInfoFirebase,
  getMasterWalletFirebase,
  transferSol,
  transferNft,
} = require("./helpers/helpers");

// Setup Express.js server
const port = process.env.PORT || 3000;
const app = express();
const fs = require("fs");
const {
  PublicKey,
  Keypair,
  Connection,
  clusterApiUrl,
} = require("@solana/web3.js");
const pinataSDK = require("@pinata/sdk");
const { AnchorProvider, Program } = require("@project-serum/anchor");
const { default: NodeWallet } = require("@project-serum/anchor/dist/cjs/nodewallet");
const JWT =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJmNzI2MjYxNS1kZjc5LTRmOGYtOTc2My1hOGFiMGIwZDJiMzQiLCJlbWFpbCI6ImF0ZDEyNDEyNUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJpZCI6IkZSQTEiLCJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MX0seyJpZCI6Ik5ZQzEiLCJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MX1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiNjU5M2FiOTZiMTQwMWVjNTdlNzEiLCJzY29wZWRLZXlTZWNyZXQiOiIxNmI5YzIxZDQ5OGY5NDkzM2ViZTRjMDJhNTk4MTM0Y2FiMjc0Njg2ZTVhZDc3NzVhNGVmZDNiNWY3NTRmYWQ0IiwiaWF0IjoxNjc3NjkxMTM5fQ.idBrYxK2i5f6w8pggFFZ-8ac8YadEYKC4sgeIMxvt9o";
const pinata = new pinataSDK({ pinataJWTKey: JWT });
app.use(bodyParser.json());
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "*");
  next();
});

app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "*");
  next();
});

app.get("/viewWalletBalance/:user_id", (req, res) => {
  try {
    const userId = req.params.user_id;
    getWalletBalanceFirebase(userId).then((result) => res.send(result));
  } catch (err) {
    console.log(err);
  }
});

app.get("/viewTransactionHistory/:user_id", (req, res) => {
  try {
    const userId = req.params.user_id;
    getTransactionHistoryFirebase(userId).then((result) => res.send(result));
  } catch (err) {
    console.log(err);
  }
});

app.get("/getUserInfo/:user_id", (req, res) => {
  const user_id = req.params.user_id;
  try {
    getUserFirebase(user_id).then((result) => res.send(result));
  } catch (err) {
    console.log(err);
  }
});

app.post("/uploadUserInfo", (req, res) => {
  // Extract user data from the request body
  const { user_id, user_handle, user_name, user_contact, chat_id } = req.body;
  const userInfo = {
    user_id,
    user_handle,
    user_name,
    user_contact,
    chat_id,
    balance : 0,
  };
  try {
    insertUserFirebase(userInfo).then(() =>
      res.status(200).json({ message: "User data successfully saved" })
    );
  } catch (err) {
    console.log(err);
  }
});

app.post("/topUpWallet", (req, res) => {
  const { user_id, amount, transaction_type, timestamp } = req.body;
  const userBalanceObject = { user_id, amount, transaction_type };
  const newTransaction = { user_id, amount, transaction_type, timestamp };
  const bankBalanceObject = { amount, transaction_type };

  try {
    updateUserBalanceFirebase(userBalanceObject)
      .then(() => insertTransactionFirebase(newTransaction))
      .then(() => updateBankBalanceFirebase(bankBalanceObject))
      .then(() => {
        console.log("Response Sent");
        res.status(200).json({ message: "Payment successfully processed" });
      });
  } catch (err) {
    console.log("/topUpWallet error", err);
  }
});

app.get("/viewEvents", (req, res) => {
  try {
    getEventsFirebase().then((result) => res.send(result));
  } catch (err) {
    console.log(err);
  }
});

app.get("/getEventRegistrations/:event_title", (req, res) => {
  const event_title = req.params.event_title;
  try {
    getEventRegistrationsFirebase(event_title).then((result) =>
      res.send(result)
    );
  } catch (err) {
    console.log(err);
  }
});

app.post("/updateRegistration", (req, res) => {
  const { user_id, event_title, status, mint_account, redemption_time } =
    req.body;
  const registrationInfo = {
    user_id,
    event_title,
    status,
    mint_account,
    redemption_time,
  };
  try {
    updateRegistrationFirebase(registrationInfo).then(() => {
      res.status(200).json({
        message: `${registrationInfo.user_id} status successfully updated to ${registrationInfo.status}`,
      });
    });
  } catch (err) {
    console.log("/updatetRegistration error", err);
  }
});

app.get("/getRegistrations/:user_id", (req, res) => {
  const user_id = req.params.user_id;
  try {
    getRegistrationsFirebase(user_id).then((result) => res.send(result));
  } catch (err) {
    console.log(err);
  }
});

app.get("/getAllRegistrations", (req, res) => {
  const user_id = req.params.user_id;
  try {
    getAllRegistrationsFirebase(user_id).then((result) => res.send(result));
  } catch (err) {
    console.log(err);
  }
});

app.post("/insertRegistration", (req, res) => {
  const { user_id, event_title, status, registration_time } = req.body;
  const registrationInfo = { user_id, event_title, status, registration_time };
  try {
    insertRegistrationFirebase(registrationInfo).then(() => {
      res
        .status(200)
        .json({ message: "User successfully registered for event" });
    });
  } catch (err) {
    console.log("/insertRegistration error", err);
  }
});

app.post("/ticketSale", (req, res) => {
  const { user_id, amount, transaction_type, timestamp, event_title } =
    req.body;
  const userBalanceObject = { user_id, amount, transaction_type };
  const newTransaction = {
    user_id,
    amount,
    transaction_type,
    timestamp,
    event_title,
  };
  const bankBalanceObject = { amount, transaction_type };

  try {
    updateUserBalanceFirebase(userBalanceObject)
      .then(() => insertTransactionFirebase(newTransaction))
      .then(() => updateBankBalanceFirebase(bankBalanceObject))
      .then(() => {
        console.log("Response Sent");
        res.status(200).json({ message: "Payment successfully processed" });
      });
  } catch (err) {
    console.log("/ticketSale error", err);
  }
});

app.post("/raffleRefund", (req, res) => {
  const { user_id, amount, transaction_type, timestamp, event_title } =
    req.body;
  const userBalanceObject = { user_id, amount, transaction_type };
  const newTransaction = {
    user_id,
    amount,
    transaction_type,
    timestamp,
    event_title,
  };
  const bankBalanceObject = { amount, transaction_type };

  try {
    updateUserBalanceFirebase(userBalanceObject)
      .then(() => insertTransactionFirebase(newTransaction))
      .then(() => updateBankBalanceFirebase(bankBalanceObject))
      .then(() => {
        console.log("Response Sent");
        res.status(200).json({ message: "Payment successfully processed" });
      });
  } catch (err) {
    console.log("/raffleRefund error", err);
  }
});

app.post("/uploadMetadata", (req, res) => {
  // Construct URI, using IPFS browser gateway
  // image_URI = req.body["image_URI"]
  // title = req.body["title"]
  // symbol = req.body["symbol"]
  const options = {
    pinataMetadata: {
      name: "test",
    },
    pinataOptions: {
      cidVersion: 0,
    },
  };
  const metadata = req.body;
  pinata
    .pinJSONToIPFS(metadata, options)
    .then((result) => {
      console.log(result["IpfsHash"]);
      res.send(result["IpfsHash"]);
    })
    .catch((err) => console.log(err));
});

// The body of the request to /mintNFT must contains an array of user_ids
// & the title of the event for which the NFT is to be minted
app.post("/mintNft", (req, res) => {
  const { user_ids, event_title } = req.body;
  try {
    handleMint(user_ids, event_title).then((result) => {
      res.status(200).json(result);
    });
  } catch (err) {
    console.log("/mintNft error ", err);
  }
});

const handleMint = async (userIds, eventTitle) => {
  const mintTransactionArray = [];
  const connection = new Connection(clusterApiUrl("devnet"), "processed");

  // Obtain keys for "master" wallet
  const masterWalletKeys = await getMasterWalletFirebase();
  const rawPrivateKey = masterWalletKeys.privateKey;
  const privateKeyArray = Uint8Array.from(
    Object.entries(rawPrivateKey).map(([key, value]) => value)
  );
  const masterKeypair = Keypair.fromSecretKey(privateKeyArray);

  // Extract arguments required for mint transaction
  const nftInfo = await getNftInfoFirebase(eventTitle);
  console.log("Nft Info: ", nftInfo)
  const { merchantKey, title, symbol, uri } = nftInfo[0];
  const creatorKey = new PublicKey(merchantKey);

  // Arguments for mintNft() call in the loop
  const TOKEN_METADATA_PROGRAM_ID = new PublicKey(
    "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
  );
  const provider = new AnchorProvider(
    connection,
    new NodeWallet(masterKeypair),
    AnchorProvider.defaultOptions()
  );
  const idl = require("./idl.json");
  const TREEHOPPERS_PROGRAM_ID = new PublicKey(
    "BgAh9RE8D5119VA1q28MxPMx77mdbYxWc7DPB5ULAB5x"
  );
  const program = new Program(idl, TREEHOPPERS_PROGRAM_ID, provider);

  for (let index in userIds) {
    userId = userIds[index];
    // Obtain keys for user's wallet
    const userWalletKeys = await getUserWalletFirebase(userId);
    const userKeypair = Keypair.fromSecretKey(userWalletKeys.privateKey);

    if (userWalletKeys.newWallet) {
      // Transfer SOL to the user's wallet
      const transferSolTransaction = await transferSol(
        masterKeypair,
        userKeypair.publicKey,
        connection
      );
    }

    // Mint the NFT to the master wallet
    const mintTransaction = await mintNft(
      masterKeypair, // userKeypair
      creatorKey,
      title,
      symbol,
      uri,
      TOKEN_METADATA_PROGRAM_ID,
      provider,
      program,
    );

    // Transfer the NFT to the User's wallet, returns a string (mint account or failure message)
    const NftTransferTransaction = await transferNft(
      masterKeypair,
      userKeypair.publicKey,
      connection,
      mintTransaction.mintAccountAddress
    );
    // mintTransactionArray.push({ [userId]: mintTransaction.mintAccountAddress });
    mintTransactionArray.push({ [userId]: NftTransferTransaction });
  }
  return mintTransactionArray;
};

// Start the Express.js web server
app.listen(port, () => console.log(`Express.js API listening on port ${port}`));
