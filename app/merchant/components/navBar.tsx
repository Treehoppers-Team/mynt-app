import { useState } from "react";
import logo from "../public/mynt.webp";
import Image from "next/image";
import dynamic from "next/dynamic";
import Link from "next/link";
import {signIn, signOut, useSession} from "next-auth/react";
import { Card, CardBody, CardFooter, Stack, Heading, Text, Button, SkeletonText, Box } from '@chakra-ui/react';
import { useRouter } from 'next/router';

const App = dynamic(
  () => {
    return import("../pages/Web3Auth");
  },
  { ssr: false }
);

interface NavLinkProps {
  to: string;
  children: React.ReactNode;
}

function NavLink({ to, children }: NavLinkProps) {
  return (
    <Link
      href={to}
      className={`flex mx-1 p-2 font-bold hover:text-gray-700 tracking-tight items-center`}
    >
      {children}
    </Link>
  );
}

interface MobileNavProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

function MobileNav({ open, setOpen }: MobileNavProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
	const loading = status === 'loading';
  const isLoggedIn = !!session?.user;
  return (
    <div
      className={`absolute top-0 left-0 h-screen w-screen bg-white transform ${
        open ? "-translate-x-0" : "-translate-x-full"
      } transition-transform duration-300 ease-in-out filter drop-shadow-md `}
    >
      <div className="flex items-center justify-center filter drop-shadow-md bg-white h-20">
        {" "}
        {/*logo container*/}
        {/* <a className="text-xl font-semibold" href="/">LOGO</a> */}
        <Link href="/">
          <Image src={logo} alt={""} width={64}></Image>
        </Link>
      </div>
      <div className="flex flex-col ml-4">
        <Link
          className="text-xl font-medium my-4"
          href="/createEvent"
          onClick={() =>
            setTimeout(() => {
              setOpen(!open);
            }, 100)
          }
        >
          Create Event
        </Link>
        <Link
          className="text-xl font-normal my-4"
          href="/about"
          onClick={() =>
            setTimeout(() => {
              setOpen(!open);
            }, 100)
          }
        >
          About
        </Link>
        <div className="flex flex-wrap">
            {loading ? null : (
              <>
                {/* {session?.user?.image ? (
                  <Image
                    height={32}
                    width={32}
                    src={session?.user?.image}
                    alt=""
                  />
                ) : null} */}
                <button
                  className="bg-[#00C48A] text-white font-bold py-2 px-4 rounded hover:bg-[#017250]"
                  onClick={(e) => {
                    e.preventDefault();
                    if (isLoggedIn) {
                      router.push("/api/auth/signout");
                      signOut();
                    } else {
                      router.push("/api/auth/signin");
                      signIn();
                    }
                  }}
                >
                  {isLoggedIn ? "Sign out" : "Sign in"}
                </button>
                <div className="flex flex-wrap items-center m-1">
                  {session?.user ? (
                    <>
                      <a>You are signed in as</a>&nbsp;
                      <a className="font-bold">
                        {session.user.email ?? session.user.name}
                      </a>
                    </>
                  ) : (
                    <a>You are not signed in</a>
                  )}
                </div>


              </>
            )}
          </div>

      </div>
    </div>
  );
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { data: session, status } = useSession();
  const router = useRouter();
	const loading = status === 'loading';
  const isLoggedIn = !!session?.user;
  return (
    <nav className="flex filter bg-blackdrop-shadow-md border-b border-black px-2 py-2 h-20 items-center">
      <MobileNav open={open} setOpen={setOpen} />
      <div className="w-1/2 flex flex-wrap items-center">
        {/* <a className="text-2xl font-semibold" href="/">LOGO</a> */}
        <Link href="/">
          <Image src={logo} alt={""} width={64}></Image>
        </Link>
        <Link
          href="/"
          className={`mx-2 p-2 text-3xl text-[#00C48A] font-bold tracking-tight`}
        >
          Mynt.
        </Link>
      </div>
      <div className="w-1/2 flex justify-end items-center">
        <div
          className="z-50 flex relative w-8 h-8 flex-col justify-between items-center md:hidden"
          onClick={() => {
            setOpen(!open);
          }}
        >
          {/* hamburger button */}
          <span
            className={`h-1 w-full bg-black rounded-lg transform transition duration-300 ease-in-out ${
              open ? "rotate-45 translate-y-3.5" : ""
            }`}
          />
          <span
            className={`h-1 w-full bg-black rounded-lg transition-all duration-300 ease-in-out ${
              open ? "w-0" : "w-full"
            }`}
          />
          <span
            className={`h-1 w-full bg-black rounded-lg transform transition duration-300 ease-in-out ${
              open ? "-rotate-45 -translate-y-3.5" : ""
            }`}
          />
        </div>

        <div className="hidden md:flex">
          <NavLink to="/createEvent">Create Event</NavLink>
          <NavLink to="/about">About</NavLink>
          <div className="flex flex-wrap">
            {loading ? null : (
              <>
                {/* {session?.user?.image ? (
                  <Image
                    height={32}
                    width={32}
                    src={session?.user?.image}
                    alt=""
                  />
                ) : null} */}
                <button
                  className="bg-[#00C48A] text-white font-bold py-2 px-4 rounded hover:bg-[#017250]"
                  onClick={(e) => {
                    e.preventDefault();
                    if (isLoggedIn) {
                      router.push("/api/auth/signout");
                      signOut();
                    } else {
                      router.push("/api/auth/signin");
                      signIn();
                    }
                  }}
                >
                  {isLoggedIn ? "Sign out" : "Sign in"}
                </button>
                <div className="flex flex-wrap items-center m-1">
                  {session?.user ? (
                    <>
                      <a>You are signed in as</a>&nbsp;
                      <a className="font-bold">
                        {session.user.email ?? session.user.name}
                      </a>
                    </>
                  ) : (
                    <a>You are not signed in</a>
                  )}
                </div>


              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
