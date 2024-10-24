import { $ } from "bun";

const nodes = [...Array(6).keys()].map((i) => i+1);
const dirs = ["a", "b", "c", "d", "e", "f"];

const ssh = (node, command) => `ssh ubuntu@node${node} ${command}`;

nodes.forEach(async node => {
  dirs.forEach(async dir => {
    const command = `ls /mnt/data/${dir}`
    const result = await $`${ssh(node, command)}`;
    console.log(result);
  }); 
});

