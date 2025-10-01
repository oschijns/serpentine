/*	simple Hello World, for cc65, for NES
 *  writing to the screen with rendering disabled
 *	using neslib
 *	Doug Fraker 2018
 */	
 
 
 
#include "neslib.h"
#include "nesdoug.h" 

// use file generated from template
#include "vector_2_fix16.h"

#define BLACK 0x0f
#define DK_GY 0x00
#define LT_GY 0x10
#define WHITE 0x30
// there's some oddities in the palette code, black must be 0x0f, white must be 0x30
 
 
 
#pragma bss-name(push, "ZEROPAGE")

// GLOBAL VARIABLES
// all variables should be global for speed
// zeropage global is even faster

u8 i;



const u8 text [] = "SnakeR!"; // zero terminated c string

const u8 palette [] =
{
	BLACK, DK_GY, LT_GY, WHITE,
	0,0,0,0,
	0,0,0,0,
	0,0,0,0
}; 


Vec2fix16 other;
	

void main (void)
{
	acc_vec_2_fix16.coords[0] = 0;
	acc_vec_2_fix16.coords[1] = 0;
	add_vec2_fix16(other);
	
	ppu_off(); // screen off

	pal_bg(palette); //	load the BG palette
		
	// set a starting point on the screen
	// vram_adr(NTADR_A(x,y));
	vram_adr(NTADR_A(10,14)); // screen is 32 x 30 tiles

	i = 0;
	while(text[i])
	{
		vram_put(text[i]); // this pushes 1 char to the screen
		++i;
	}	
	
	// vram_adr and vram_put only work with screen off
	// NOTE, you could replace everything between i = 0; and here with...
	// vram_write(text,sizeof(text));
	// does the same thing
	
	ppu_on_all(); //	turn on screen
	
	
	while (1)
	{
		// infinite loop
		// game code can go here later.
		
	}
}
	
	