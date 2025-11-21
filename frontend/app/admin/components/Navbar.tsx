type NavbarProps = {
  title?: string;
};

export default function Navbar({ title = "Admin" }: NavbarProps) {
  return (
    <div className="fixed h-16 z-40 inset-x-0 top-0 bg-gradient-to-b from-secondary/30 from-[30%] to-transparent">
      <header className="z-50 fixed shadow-sm top-2 inset-x-2 bg-secondary/50 backdrop-blur-xs rounded-sm h-12"></header>
    </div>
  )
}
