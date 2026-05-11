type Props = {
  message: string
}

export default function LoadingState({ message }: Props) {
  return (
    <section className="panel">
      <p>{message}</p>
    </section>
  )
}
