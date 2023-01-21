import Head from "next/head";
import { Inter } from "@next/font/google";
import styles from "@/styles/Home.module.css";
import Card from "@/components/card";
import { useEffect, useState } from "react";


const inter = Inter({ subsets: ["latin"] });

export default function Home() {
  const [loading, setLoading] = useState<boolean>(true);
  const [events, setEvents] = useState<any>({});

  let cards: JSX.Element[] = [];

  function generateCards(events: string | any[]) {
      for (let i = 0; i < events.length; i++) {
        cards.push(
          <div key={i} className="m-2">
            <Card 
            key={i} 
            title={events[i].title} 
            description={events[i].description}
            price={events[i].price}
            time={events[i].time}
            venue={events[i].venue}
            capacity={events[i].capacity}
            />
          </div>
        );
      }
      return cards

    }
  

  const cardSection = (body: any) => {
    return <div className="flex flex-wrap justify-center">{body}</div>;
  };

  // make an api call to /viewEvents to get all the events created by the merchant
  // then map the events to the card component

  async function getEvents() {
    const res = await fetch("http://localhost:3000/viewEvents");
    const data = await res.json();
    setLoading(false);
    return data;
  }

  useEffect(() => {
    getEvents().then((res) => {
      console.log(res)
      console.log(loading)
      setEvents(res);
    })
  },[])

  return (
    <>
      <Head>
        <title>Merchant Dashboard</title>
        <meta name="description" content="Generated by create next app" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <h1 className="px-6 py-6 text-4xl font-bold text-center">
          Events Created
        </h1>
        {loading==false ? cardSection(generateCards(events)) : null}
      </main>

    </>
  );
}