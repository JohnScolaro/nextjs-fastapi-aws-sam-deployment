import PageClient from "./components/page_client";
import { use } from 'react'

type Params = Promise<{ key: string }>
type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>

export default function Page(props: {
  params: Params
  searchParams: SearchParams
}) {
  return (<PageClient params={use(props.params)}></PageClient>)
}

export async function generateStaticParams() {
  return [
    { key: 'cumulative_time' },
    { key: 'cumulative_distance' }
  ];
}